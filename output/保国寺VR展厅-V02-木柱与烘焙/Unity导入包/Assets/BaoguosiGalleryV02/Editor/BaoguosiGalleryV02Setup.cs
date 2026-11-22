#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

// Editor-only. No network, paid package, XR SDK or render-pipeline dependency.
// Leaves project lighting, pipeline, current scenes and existing assets unchanged.
[InitializeOnLoad]
public static class BaoguosiGalleryV02Setup
{
    public const string Root = "Assets/BaoguosiGalleryV02";
    const string ModelPath = Root + "/Models/Baoguosi_Gallery_V02_Baked.fbx";
    static bool queued;
    static bool working;

    static BaoguosiGalleryV02Setup() { QueueSetup(); }

    public static void QueueSetup()
    {
        if (queued || working) return;
        queued = true;
        EditorApplication.delayCall += () => {
            queued = false;
            if (EditorApplication.isCompiling || EditorApplication.isUpdating) { QueueSetup(); return; }
            try { ConfigureMaterials(false); }
            catch (Exception e) { Debug.LogError("保国寺展厅材质配置未完成：" + e.Message); }
        };
    }

    static Shader DisplayShader()
    {
        var pipeline = GraphicsSettings.currentRenderPipeline;
        bool urp = pipeline != null && pipeline.GetType().Name.IndexOf("Universal", StringComparison.OrdinalIgnoreCase) >= 0;
        if (pipeline != null && !urp)
            throw new InvalidOperationException("当前项目不是 Built-in 或 URP。请使用这两种管线之一；工具不会自动更换项目管线。");
        Shader shader = Shader.Find(urp ? "Universal Render Pipeline/Unlit" : "Unlit/Texture");
        if (shader == null) throw new InvalidOperationException("找不到当前管线的 Unlit 材质，请确认渲染管线已正确安装。");
        return shader;
    }

    static void Folder(string path)
    {
        if (AssetDatabase.IsValidFolder(path)) return;
        Folder(Path.GetDirectoryName(path).Replace('\\', '/'));
        AssetDatabase.CreateFolder(Path.GetDirectoryName(path).Replace('\\', '/'), Path.GetFileName(path));
    }

    static Texture2D LoadAtlas(string path)
    {
        var importer = AssetImporter.GetAtPath(path) as TextureImporter;
        if (importer == null) throw new FileNotFoundException("缺少烘焙贴图：" + path);
        bool changed = !importer.sRGBTexture || !importer.mipmapEnabled || importer.maxTextureSize != 4096 || importer.alphaSource != TextureImporterAlphaSource.None;
        var android = importer.GetPlatformTextureSettings("Android");
        if (!android.overridden || android.format != TextureImporterFormat.ASTC_6x6 || android.maxTextureSize != 4096)
        {
            android.overridden = true;
            android.format = TextureImporterFormat.ASTC_6x6;
            android.maxTextureSize = 4096;
            importer.SetPlatformTextureSettings(android);
            changed = true;
        }
        if (changed)
        {
            importer.sRGBTexture = true;
            importer.mipmapEnabled = true;
            importer.maxTextureSize = 4096;
            importer.alphaSource = TextureImporterAlphaSource.None;
            importer.textureCompression = TextureImporterCompression.Compressed;
            importer.SaveAndReimport();
        }
        return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
    }

    static Material MakeMaterial(string name, Texture2D texture, Shader shader)
    {
        string path = Root + "/Materials/" + name + ".mat";
        Material mat = AssetDatabase.LoadAssetAtPath<Material>(path);
        bool dirty = mat == null;
        if (mat == null) { mat = new Material(shader); mat.name = name; AssetDatabase.CreateAsset(mat, path); }
        if (mat.shader != shader) { mat.shader = shader; dirty = true; }
        foreach (string property in new[] { "_MainTex", "_BaseMap" })
            if (mat.HasProperty(property) && mat.GetTexture(property) != texture) { mat.SetTexture(property, texture); dirty = true; }
        if (mat.HasProperty("_BaseColor") && mat.GetColor("_BaseColor") != Color.white) { mat.SetColor("_BaseColor", Color.white); dirty = true; }
        if (mat.HasProperty("_Color") && mat.GetColor("_Color") != Color.white) { mat.SetColor("_Color", Color.white); dirty = true; }
        if (dirty) { mat.enableInstancing = true; mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None; EditorUtility.SetDirty(mat); }
        return mat;
    }

    [MenuItem("榫卯智言/展厅V02/1 配置或修复烘焙材质")]
    public static void RepairMaterials() { ConfigureMaterials(true); }

    static void ConfigureMaterials(bool showResult)
    {
        if (working || !File.Exists(ModelPath)) return;
        working = true;
        try
        {
            Shader shader = DisplayShader();
            Folder(Root + "/Materials");
            var importer = AssetImporter.GetAtPath(ModelPath) as ModelImporter;
            if (importer == null) return;
            bool reimport = false;
            if (importer.materialImportMode != ModelImporterMaterialImportMode.ImportStandard) { importer.materialImportMode = ModelImporterMaterialImportMode.ImportStandard; reimport = true; }
            if (importer.importCameras) { importer.importCameras = false; reimport = true; }
            if (importer.importLights) { importer.importLights = false; reimport = true; }
            if (importer.importAnimation) { importer.importAnimation = false; reimport = true; }
            if (importer.generateSecondaryUV) { importer.generateSecondaryUV = false; reimport = true; }
            var external = importer.GetExternalObjectMap();
            for (int zone = 1; zone <= 8; zone++)
            {
                string name = "BG_Baked_Zone" + zone.ToString("00");
                Texture2D atlas = LoadAtlas(Root + "/Textures/Baked_Zone" + zone.ToString("00") + ".png");
                Material material = MakeMaterial(name, atlas, shader);
                var id = new AssetImporter.SourceAssetIdentifier(typeof(Material), name);
                UnityEngine.Object mapped;
                if (!external.TryGetValue(id, out mapped) || mapped != material) { importer.AddRemap(id, material); reimport = true; }
            }
            // Preserve vector wall lettering; a one-pixel texture keeps both stock
            // Unlit shaders consistent, including Built-in's texture-only shader.
            Texture2D ink = LoadAtlas(Root + "/Textures/Ink.png");
            Material inkMaterial = MakeMaterial("BG_Ink", ink, shader);
            var inkId = new AssetImporter.SourceAssetIdentifier(typeof(Material), "BG_Ink");
            UnityEngine.Object inkMapped;
            if (!external.TryGetValue(inkId, out inkMapped) || inkMapped != inkMaterial) { importer.AddRemap(inkId, inkMaterial); reimport = true; }
            Texture2D bronze = LoadAtlas(Root + "/Textures/Bronze.png");
            Material bronzeMaterial = MakeMaterial("BG_Bronze", bronze, shader);
            var bronzeId = new AssetImporter.SourceAssetIdentifier(typeof(Material), "BG_Bronze");
            UnityEngine.Object bronzeMapped;
            if (!external.TryGetValue(bronzeId, out bronzeMapped) || bronzeMapped != bronzeMaterial) { importer.AddRemap(bronzeId, bronzeMaterial); reimport = true; }
            AssetDatabase.SaveAssets();
            if (reimport) importer.SaveAndReimport();
            if (showResult) EditorUtility.DisplayDialog("保国寺展厅 V02", "8 张光影贴图和墙面文字材质已配置。\n下一步：菜单 2 创建展厅场景。", "确定");
        }
        finally { working = false; }
    }

    [MenuItem("榫卯智言/展厅V02/2 创建展厅场景（无摄像机）")]
    public static void CreateGalleryScene()
    {
        ConfigureMaterials(false);
        GameObject asset = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
        if (asset == null) { EditorUtility.DisplayDialog("保国寺展厅", "模型尚未导入，请等待导入完成。", "确定"); return; }
        Folder(Root + "/Scenes");
        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Additive);
        SceneManager.SetActiveScene(scene);
        GameObject gallery = (GameObject)PrefabUtility.InstantiatePrefab(asset, scene);
        gallery.name = "保国寺数字斗拱展厅 V02（静态光影）";
        // Existing XR rigs can be added later; no Camera, light or global volume is created.
        foreach (Renderer renderer in gallery.GetComponentsInChildren<Renderer>())
        {
            renderer.shadowCastingMode = ShadowCastingMode.Off;
            renderer.receiveShadows = false;
        }
        string scenePath = AssetDatabase.GenerateUniqueAssetPath(Root + "/Scenes/BaoguosiGalleryV02.unity");
        EditorSceneManager.SaveScene(scene, scenePath);
        Selection.activeGameObject = gallery;
        if (SceneView.lastActiveSceneView != null)
        {
            // Enter the interior at eye level. Do not leave the editor looking
            // down at an opaque roof. Named anchors avoid assumptions about
            // the FBX importer's handedness and axis conversion.
            var transforms = gallery.GetComponentsInChildren<Transform>();
            Transform exhibit = transforms.FirstOrDefault(t => t.name == "P01_ExhibitAnchor_EMPTY");
            Transform title = transforms.FirstOrDefault(t => t.name == "Title05_Main");
            if (exhibit != null && title != null)
            {
                Vector3 horizontal = Vector3.ProjectOnPlane(title.position - exhibit.position, Vector3.up).normalized;
                Vector3 eye = exhibit.position - horizontal * 3.9f;
                eye.y = exhibit.position.y + 1.44f;
                Vector3 target = title.position - Vector3.up * 1.1f;
                SceneView.lastActiveSceneView.LookAt(target, Quaternion.LookRotation(target - eye, Vector3.up), Vector3.Distance(eye, target) * 0.5f, false);
            }
        }
        EditorUtility.DisplayDialog("展厅场景已创建", "场景已另存；原有场景未关闭。\n本场景无摄像机、无实时灯光。接入自己的 XR Origin 后即可从头盔视角查看。\n请关闭或调整项目已有的全局曝光/色调映射，以免静态光影被二次处理。", "确定");
    }

    [MenuItem("榫卯智言/展厅V02/3 检查已导入资源")]
    public static void ValidateImportedResources()
    {
        GameObject asset = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
        if (asset == null) throw new InvalidOperationException("模型尚未导入。");
        Shader expected = DisplayShader();
        var renderers = asset.GetComponentsInChildren<Renderer>();
        int bad = 0;
        foreach (Renderer renderer in renderers)
            foreach (Material mat in renderer.sharedMaterials)
            {
                if (mat == null || mat.shader != expected) { bad++; continue; }
                string property = mat.HasProperty("_BaseMap") ? "_BaseMap" : "_MainTex";
                if (mat.GetTexture(property) == null) bad++;
            }
        int cameras = asset.GetComponentsInChildren<Camera>(true).Length;
        int lights = asset.GetComponentsInChildren<Light>(true).Length;
        string result = "渲染网格：" + renderers.Length + "\n异常材质/贴图：" + bad + "\n模型摄像机：" + cameras + "\n模型灯光：" + lights + "\n当前显示材质：" + expected.name;
        bool ok = bad == 0 && cameras == 0 && lights == 0 && renderers.Length > 0;
        Debug.Log("保国寺展厅导入检查（" + (ok ? "通过" : "需检查") + "）\n" + result);
        EditorUtility.DisplayDialog(ok ? "导入检查通过" : "请先修复材质或资源", result + "\n此检查不代替头盔实机性能测试。", "确定");
    }
}

public sealed class BaoguosiGalleryV02AssetWatcher : AssetPostprocessor
{
    static void OnPostprocessAllAssets(string[] imported, string[] deleted, string[] moved, string[] movedFrom)
    {
        if (imported.Any(path => path.StartsWith(BaoguosiGalleryV02Setup.Root + "/Models/", StringComparison.Ordinal) || path.StartsWith(BaoguosiGalleryV02Setup.Root + "/Textures/", StringComparison.Ordinal)))
            BaoguosiGalleryV02Setup.QueueSetup();
    }
}
#endif
