using System;
using System.IO;
using System.Diagnostics;


namespace hashtopolis
{

    class _7zClass
    {

        public class dlProps
        {
            public string action = "downloadBinary";
            public string type = "7zr";
            public string token { get; set; }
        }

        public int osID { get; set; }
        public string tokenID { get; set; }
        public string appPath { get; set; }
        public string connectURL { get; set; }

        string binPath = "";

        public Boolean init7z()
        {

            binPath = Path.Combine(appPath, "7zr");
            if (osID == 1)
            {
                binPath += ".exe";
            }

            if (!File.Exists(binPath))
            {
                Console.WriteLine("Downloading 7zip binary");
                jsonClass jsC = new jsonClass { debugFlag = true, connectURL = connectURL };

                dlProps dlzip = new dlProps
                {
                    token = tokenID
                };


                string jsonString = jsC.toJson(dlzip);
                string ret = jsC.jsonSend(jsonString);
                if (jsC.isJsonSuccess(ret))

                {
                    string dlLocation = jsC.getRetVar(ret,"executable");
                    downloadClass dlClass = new downloadClass();

                    if (!dlClass.DownloadFile(dlLocation, binPath))
                    {
                        Console.WriteLine("Unable to download requested file");
                    }
                    else
                    {
                        Console.WriteLine("Finished downloading file");
                    }
                    
                }
                if (osID != 1) //If OS is not windows, we need to set the permissions
                {
                    try
                    {
                        Console.WriteLine("Applying execution permissions to 7zr binary");
                        Process.Start("chmod", "+x \"" + binPath + "\"");
                    }
                    catch (Exception e)
                    {
                        Console.Write(e.Data);
                        Console.WriteLine("Unable to change access permissions of 7zr, execution permissions required");
                    }
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
            pinfo.Arguments = " x -y -o\"" + outDir + "\" \"" + archivePath + "\"";

            Process unpak = new Process();
            unpak.StartInfo = pinfo;

            if (files != "") unpak.StartInfo.Arguments += " " + files;

            Console.WriteLine(pinfo.FileName + pinfo.Arguments);
            Console.WriteLine("Extracting archive " + archivePath + "...");

            FileInfo f = new FileInfo(archivePath);

            if (f.Length == 0)
            {
                Console.WriteLine("File is 0 bytes");
                return false;
            }

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
