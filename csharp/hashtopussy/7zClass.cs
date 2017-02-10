using System;
using System.IO;
using System.Diagnostics;


namespace hashtopussy
{


    class _7zClass
    {

        public class dlProps
        {
            public string action = "download";
            public string type = "7zr";
            public string token { get; set; }
        }

        int osID = 0;
        string binPath = "";
        string appPath = "";

        public Boolean init7z(string path, int os, string tokenString)
        {

            osID = os;
            appPath = path;

            dlProps dlzip = new dlProps
            {
                token = tokenString
            };


            binPath = Path.Combine(path, "7zr");
            if (os == 1)
            {
                binPath += ".exe";
            }


            if (!File.Exists(binPath))
            {
                jsonClass jsC = new jsonClass();
                string jsonString = jsC.toJson(dlzip);
                string ret = jsC.jsonSend(jsonString);

                if (ret[0] != '{' && ret[ret.Length - 1] != '}')
                {
                    File.WriteAllText(binPath, ret);
                }

            }

            if (File.Exists(binPath))
            {
                return true;
            }

            return false;
            
        }

        //Code from hashtopus
        public Boolean xtract(string archivePath, string outDir, string files = "")
        {
            ProcessStartInfo pinfo = new ProcessStartInfo();
            pinfo.FileName = binPath;
            pinfo.WorkingDirectory = appPath;
            pinfo.Arguments = "x -y -o\"" + outDir + "\" \"" + archivePath + "\"";

            Process unpak = new Process();
            unpak.StartInfo = pinfo;

            if (files != "") unpak.StartInfo.Arguments += " " + files;

            Console.WriteLine("Extracting archive " + archivePath + "...");

            try
            {
                if (!unpak.Start()) return false;
            }
            catch
            {
                Console.WriteLine("Could not start 7zr.");
                return false;
            }
            finally
            {
                unpak.WaitForExit();
            }
            
            return true;

        }
    }
}
