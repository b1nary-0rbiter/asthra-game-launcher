using UnityEditor;
using UnityEditor.Build.Reporting;
using System.IO;
using System.Linq;

namespace Rhythia.Build
{
    public static class BuildWindows
    {
        [MenuItem("Rhythia/Build Windows")]
        public static void Build()
        {
            string[] scenes = EditorBuildSettings.scenes
                .Where(s => s.enabled)
                .Select(s => s.path)
                .ToArray();

            if (scenes.Length == 0)
            {
                // fallback: grab all .unity files under Assets/
                scenes = Directory.GetFiles("Assets", "*.unity", SearchOption.AllDirectories);
            }

            string buildDir = "Build";
            Directory.CreateDirectory(buildDir);
            string exePath = Path.Combine(buildDir, Path.GetFileName(EditorApplication.applicationPath).Replace("Unity", PlayerSettings.productName));

            var opts = new BuildPlayerOptions
            {
                scenes            = scenes,
                locationPathName  = exePath,
                target            = BuildTarget.StandaloneWindows64,
                options            = BuildOptions.None,
            };

            BuildReport report = BuildPipeline.BuildPlayer(opts);
            BuildSummary summary = report.summary;

            if (summary.result != BuildResult.Succeeded)
            {
                EditorApplication.Exit(1);
            }
        }
    }

    public static class BuildLinux
    {
        [MenuItem("Rhythia/Build Linux")]
        public static void Build()
        {
            string[] scenes = EditorBuildSettings.scenes
                .Where(s => s.enabled)
                .Select(s => s.path)
                .ToArray();

            if (scenes.Length == 0)
            {
                scenes = Directory.GetFiles("Assets", "*.unity", SearchOption.AllDirectories);
            }

            string buildDir = "Build";
            Directory.CreateDirectory(buildDir);
            string exePath = Path.Combine(buildDir, PlayerSettings.productName + ".x86_64");

            var opts = new BuildPlayerOptions
            {
                scenes            = scenes,
                locationPathName  = exePath,
                target            = BuildTarget.StandaloneLinux64,
                options            = BuildOptions.None,
            };

            BuildReport report = BuildPipeline.BuildPlayer(opts);
            BuildSummary summary = report.summary;

            if (summary.result != BuildResult.Succeeded)
            {
                EditorApplication.Exit(1);
            }
        }
    }
}