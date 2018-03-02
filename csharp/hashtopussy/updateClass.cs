using System;
using System.Diagnostics;
using System.Threading;
using System.IO;


namespace hashtopolis
{



    public class updateClass
    {


        public string htpVersion { set; get; }
        private string parentProc;
        public string parentPath { set; get; }
        public string[] arguments { set; get; }
        public string connectURL { get; set; }
        public Boolean debugFlag { set; get; }
        public string tokenID { get; set; }

        private string launcherProcName = "HTPLauncherUpd.exe";


        private class updProps
        {
            public string action = "checkClientVersion";
            public string version { get; set; }
            public string type = "csharp";
            public string token  { get; set; }

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
                    parentProc = "hashtopolis.exe";
                }

                waitForProcess(parentProc);
                File.Copy(launcherProcName, parentProc, true);
                

                if (Type.GetType("Mono.Runtime") != null)
                {
                    Console.WriteLine("Client has now been updated, please re-launch the agent");
                }
                else
                {
                    Process reSpawn = new Process();
                    reSpawn.StartInfo.FileName = parentProc;
                    reSpawn.Start();
                    
                }
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
                    version = htpVersion,
                    token = tokenID
                };

                jsonClass jsC = new jsonClass { debugFlag = debugFlag, connectURL = connectURL };
                string jsonString = jsC.toJson(uProps);
                string ret = jsC.jsonSend(jsonString);

                if (jsC.isJsonSuccess(ret))
                {
                    if (jsC.getRetVar(ret, "version") == "OK")
                    {
                        Console.WriteLine("You are using the latest client version");
                        return;
                    }
                    else
                    {
                        downloadClass dl = new downloadClass();
                        string dlFrom = Path.Combine(jsC.getRetVar(ret, "url"));
                        string dlTo = Path.Combine(parentPath, launcherProcName);
                        dl.DownloadFile(dlFrom, dlTo);
                        Console.WriteLine("Finished downloading latest client");
                        Console.WriteLine("Client will now relaunch");
                        Process Spawn = new Process();
                        Spawn.StartInfo.WorkingDirectory = parentPath;
                        if (Type.GetType("Mono.Runtime") != null)
                        {
                            Spawn.StartInfo.FileName = "mono";
                            Spawn.StartInfo.Arguments = launcherProcName + " " +  parentProc;
                        }
                        else
                        {
                            Spawn.StartInfo.FileName = launcherProcName;
                            Spawn.StartInfo.Arguments = parentProc;
                        }

                        Spawn.Start();
                        Environment.Exit(0);
                    }
                }
                else
                {
                    Console.WriteLine("Exiting agnet");
                    Environment.Exit(0);
                }

                
               
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