using System;
using System.Diagnostics;
using System.Threading;
using System.IO;


namespace hashtopussy
{


    public class updateClass
    {

        public string htpVersion { set; get; }
        private string parentProc;
        public string parentPath { set; get; }
        public string[] arguments { set; get; }

        private string launcherProcName = "HTPLauncherUpd.exe";


        private class updProps
        {
            public string action = "update";
            public string version { get; set; }
            public string type = "csharp";

        }

        public void setParent(string strParentProc)
        {
            parentProc = strParentProc;
        }

        public void runUpdate()
	    {
        
            string currentBin = Environment.GetCommandLineArgs()[0]; //Grab current bin name

            if (System.AppDomain.CurrentDomain.FriendlyName == launcherProcName) 
            {


                for (int i = 0; i < arguments.Length; i++)
                {
                    if (arguments[i] != "debug")
                    {
                        parentProc = (arguments[i]);
                        break;
                    }
                    
                }

                //Looks like user isn't using custom name, use the default one
                if (string.IsNullOrEmpty(parentProc))
                {
                    parentProc = "hashtopussy.exe";
                }

                waitForProcess(parentProc);
                File.Copy(launcherProcName, parentProc, true);
                Process reSpawn = new Process();

                if (Type.GetType("Mono.Runtime") != null)
                {
                    reSpawn.StartInfo.FileName = "mono";
                    reSpawn.StartInfo.Arguments = parentProc;
                }
                else
                {
                    reSpawn.StartInfo.FileName = parentProc;
                }
                reSpawn.Start();
                Environment.Exit(0);
            }
            else //We are either user-run bin or spanwed bin
            {


                waitForProcess(launcherProcName);
                if (File.Exists(launcherProcName))
                {
                    Console.WriteLine("Cleaning up files post update");
                    File.Delete(launcherProcName);
                }

                Console.WriteLine("Checking for client updates");
                updProps uProps = new updProps
                {
                    version = htpVersion
                };

                jsonClass jsC = new jsonClass { debugFlag = true };
                string jsonString = jsC.toJson(uProps);
                string ret = jsC.jsonSend(jsonString);

                jsC.isJsonSuccess(ret);
                Console.WriteLine(jsC.getRetVar(ret, "url"));
                downloadClass dl = new downloadClass();
                string dlFrom = Path.Combine(jsC.getRetVar(ret, "url"));
                string dlTo = Path.Combine(parentPath, launcherProcName);
                dl.DownloadFile(dlFrom, dlTo);
                Console.WriteLine("Finished DL");

                //Check whether we need updating
                //Need code to send current version to server, probably a hash?
                //Download the launcher
                //Need to process res and download 

                //Run the launcher and exit current
                Console.WriteLine("Relaunching");
                Process Spawn = new Process();
                if (Type.GetType("Mono.Runtime") != null)
                {
                    Spawn.StartInfo.FileName = "mono";
                    Spawn.StartInfo.Arguments = launcherProcName + currentBin;
                }
                else
                {
                    Spawn.StartInfo.FileName = launcherProcName;
                    Spawn.StartInfo.Arguments =  currentBin;
                }

                Spawn.Start();
                Environment.Exit(0);
               
            }
        }


        private Boolean waitForProcess(string procName)
        {
            Process[] proc = Process.GetProcessesByName(procName);
            while (proc.Length != 0)
            {
                Thread.Sleep(500);
                proc = Process.GetProcessesByName(procName);
                Console.WriteLine("Waiting for parent");
            }
            return true;
        }
    }
}