// SPDX-License-Identifier: GPL-3.0-or-later
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
import com.google.gson.*;
import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;
import me.fengming.vaultpatcher_asm.config.*;
import me.fengming.vaultpatcher_asm.core.transformers.VPClassTransformer;
public class TransformAudit {
 static List<String> strings(ClassNode n) {
  List<String> out=new ArrayList<>();
  for (FieldNode f:n.fields) if(f.value instanceof String) out.add((String)f.value);
  for (MethodNode m:n.methods) for(AbstractInsnNode a:m.instructions) {
   if(a instanceof LdcInsnNode l && l.cst instanceof String) out.add((String)l.cst);
   if(a instanceof InvokeDynamicInsnNode d && d.name.equals("makeConcatWithConstants")) for(Object v:d.bsmArgs) if(v instanceof String) out.add((String)v);
  }
  return out;
 }
 public static void main(String[] args) throws Exception {
  me.fengming.vaultpatcher_asm.core.utils.Utils.debug.setUseCache(false);
  Map<String,byte[]> classes=new HashMap<>();
  try(var paths=Files.list(Path.of(args[1]))) { for(Path p:paths.filter(p->p.toString().endsWith(".jar")).toList()) try(ZipFile z=new ZipFile(p.toFile())) {
   for(var e:Collections.list(z.entries())) if(e.getName().endsWith(".class")) classes.put(e.getName().replace('/','.').replace(".class",""),z.getInputStream(e).readAllBytes());
  }}
  int total=0,passed=0;List<String> failures=new ArrayList<>();
  try(var paths=Files.list(Path.of(args[0]))) {for(Path p:paths.filter(p->p.toString().endsWith(".json")).toList()) {
   JsonArray blocks=JsonParser.parseString(Files.readString(p)).getAsJsonArray();
   for(int bi=1;bi<blocks.size();bi++) {
    JsonObject b=blocks.get(bi).getAsJsonObject();JsonElement target=b.has("target_class")?b.get("target_class"):b.get("target_classes");
    JsonArray targets=target.isJsonArray()?target.getAsJsonArray():new JsonArray();if(!target.isJsonArray())targets.add(target);
    for(JsonElement pe:b.getAsJsonArray("pairs")) {
     total++;JsonObject pair=pe.getAsJsonObject();String key=pair.get("key").getAsString(),value=pair.get("value").getAsString();boolean changed=false;
     for(JsonElement te:targets) {
      String t=te.getAsString();ClassNode n=new ClassNode();new ClassReader(classes.get(t)).accept(n,0);List<String> before=strings(n);
      Pairs pairs=new Pairs(false);pairs.setKey(key);pairs.setValue(value);
      new VPClassTransformer(Set.of(new TranslationInfo(t,new TargetClassInfo(),pairs))).accept(n);
      List<String> after=strings(n);
      if(!before.equals(after)) {
       if(after.stream().noneMatch(s->s.contains(value)))throw new AssertionError("Missing output: "+key);
       ClassWriter w=new ClassWriter(0);n.accept(w);new ClassReader(w.toByteArray());changed=true;
      }
     }
     if(changed)passed++;else failures.add(p.getFileName()+": "+key);
    }
   }
  }}
  System.out.println(new GsonBuilder().setPrettyPrinting().create().toJson(Map.of("pairs",total,"changed",passed,"failures",failures,"gameStarted",false)));
  if(total!=passed)System.exit(1);
 }
}
