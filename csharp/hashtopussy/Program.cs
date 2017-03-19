using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Diagnostics;
namespace hashtopussy
{

    

    public struct Packets
    {
        public Dictionary<string, double> statusPackets;
        public List<string> crackedPackets;
    }

    public class testProp
    {
        public string action = "test";
    }

    public class hcUpdateProp
    {
        public string action = "download";
        public string type = "hashcat";
        public string token = "";
        public int force { set; get; }
    }

    class Program
    {

        public static string AppPath = AppDomain.CurrentDomain.BaseDirectory;
        private static string urlPath = Path.Combine(AppPath, "URL");
        private static string serverURL = "";

        static void initDirs()
        {

            string[] createDirs = new String[] { "files", "hashlists", "tasks", "hashcat" };

            foreach (string dir in createDirs)
            {
                string enumDir = Path.Combine(AppPath, dir);
                try
                {
                    if (!Directory.Exists(enumDir))
                    {
                        Console.WriteLine("Creating {0} directory", dir);
                        Directory.CreateDirectory(enumDir);
                    }
                }
                catch(Exception e)
                {
                    Console.WriteLine(e.Data);
                    Console.WriteLine("Unable to create dir {0}", dir);
                    Console.WriteLine("Client now terminating");
                    Environment.Exit(0);
                }

            }

        }


        public static bool loadURL()
        {
            if (File.Exists(urlPath))
            {
                serverURL = File.ReadAllText(urlPath);
                if (serverURL == "")
                {
                    File.Delete(urlPath);
                    return false;
                }
            }
            else
            {
                return false;
            }
            return true;
        }


        public static Boolean initConnect()
        {
            jsonClass testConnect = new jsonClass { debugFlag = DebugMode };
            testProp tProp = new testProp();
            string urlMsg = "Please enter server connect URL (https will be used unless specified):";
            while (!loadURL())
            {
                Console.WriteLine(urlMsg);
                string url = Console.ReadLine();
                if (!url.StartsWith("http", StringComparison.OrdinalIgnoreCase))
                {
                    url = "https://" + url;
                }
                Console.WriteLine("Testing connection to " + url);
                testConnect.connectURL = url;
                string jsonString = testConnect.toJson(tProp);
                string ret = testConnect.jsonSendOnce(jsonString);
                if (ret != null)
                {
                    if (testConnect.isJsonSuccess(ret))
                    {
                        File.WriteAllText(urlPath, url);
                    }
                }
                else
                {
                    urlMsg = "Test connect failed, please enter server connect URL:";
                }

            }

            return true;
        }

        public static Boolean DebugMode;

        static void Main(string[] args)
        {

            System.Globalization.CultureInfo customCulture = (System.Globalization.CultureInfo)System.Threading.Thread.CurrentThread.CurrentCulture.Clone();
            customCulture.NumberFormat.NumberDecimalSeparator = ".";
            System.Threading.Thread.CurrentThread.CurrentCulture = customCulture;

            for (int i = 0; i < args.Length; i++)
            {
                if (args[i] == "debug")
                {
                    DebugMode = true;
                    break;
                }

            }

            string AppVersion = "0.43.7";
            Console.WriteLine("Client Version " + AppVersion);

            initConnect();

            updateClass updater = new updateClass
            {
                htpVersion = AppVersion,
                parentPath = AppPath,
                arguments = args,
                connectURL = serverURL,
                debugFlag = DebugMode
                
            };
            updater.runUpdate();

            initDirs();

            registerClass client = new registerClass { connectURL = serverURL, debugFlag = DebugMode };
            client.setPath( AppPath);
            if (client.loginAgent())
            {
                Console.WriteLine("Logged in to server");
            }

            //Run code to self-update

            _7zClass zipper = new _7zClass
            {
                tokenID = client.tokenID,
                osID = client.osID,
                appPath = AppPath,
                connectURL = serverURL
            };

            if (!zipper.init7z())
            {
                Console.WriteLine("Failed to initialize 7zip, proceeding without. \n The client may not be able to extract compressed files");
            }
            else //We have 7zip, lets check for HC update since that is zipped
            {
                hcUpdateProp hcUpd = new hcUpdateProp();
                jsonClass jsonUpd = new jsonClass { debugFlag = DebugMode, connectURL = serverURL };
                hcUpd.token = client.tokenID;
                string hcBinName = "hashcat";
                if (client.osID == 0)
                {
                    hcBinName = hcBinName + "64.bin";
                }
                else if (client.osID == 1)
                {
                    hcBinName = hcBinName + "64.exe";
                }

                string hcBinLoc = Path.Combine(AppPath, "hashcat",hcBinName);

                if (File.Exists(hcBinLoc))
                {
                    hcUpd.force = 0; //HC exists, we don't need to force
                }
                else
                {
                    hcUpd.force = 1; //HC doesn't exist, we need to force
                }

                string jsonString = jsonUpd.toJson(hcUpd);
                string ret = jsonUpd.jsonSend(jsonString);

                if (jsonUpd.getRetVar(ret,"version") == "NEW")
                {
                    downloadClass dlClass = new downloadClass();

                    if (client.osID != 1)
                    {
                        dlClass.DownloadFileCurl(jsonUpd.getRetVar(ret, "url"), Path.Combine(AppPath, "hcClient.7z"));
                    }
                    else
                    {
                        dlClass.DownloadFile(jsonUpd.getRetVar(ret, "url"), Path.Combine(AppPath, "hcClient.7z"));
                    }

                    zipper.xtract(Path.Combine(AppPath, "hcClient.7z"), Path.Combine(AppPath, "hcClient"));
                    if (Directory.Exists(Path.Combine(AppPath, "hashcat")))
                    {
                        Directory.Delete(Path.Combine(AppPath, "hashcat"), true);
                    }
                    Directory.Move(Path.Combine(AppPath, "hcClient", jsonUpd.getRetVar(ret, "rootdir")), Path.Combine(AppPath, "hashcat"));
                    Directory.Delete(Path.Combine(AppPath, "hcClient"));



                    if (client.osID != 1) //Chmod for non windows
                    {
                        Console.WriteLine("Applying execution permissions to 7zr binary");
                        Process.Start("chmod", "+x \"" + hcBinLoc + "\"");
                    }
                }

                //Double check just incase
                if (!File.Exists(hcBinLoc))
                {
                    Console.WriteLine("Could not locate {0} binary in hashcat directory", hcBinName);
                    Console.WriteLine("You can manually download and extract hashcat");
                    Console.WriteLine("Client will now terminate");
                    {
                        Environment.Exit(0);
                    }
                }
                else
                {
                    hashcatClass hcClass = new hashcatClass { };
                    hcClass.setDirs(AppPath, client.osID);
                    string hcVersion = (hcClass.getVersion());
                    Console.WriteLine("Hashcat version {0} found",hcVersion);
                }
            }

            taskClass tasks = new taskClass
            {
                tokenID = client.tokenID,
                osID = client.osID,
                sevenZip = zipper,
                connectURL = serverURL,
                debugFlag = DebugMode

            };
                
            tasks.setDirs(AppPath);
            
            int backDown = 5;
            while(true) //Keep waiting for 5 seconds and checking for tasks
            {
                Thread.Sleep(backDown * 1000);

                if (tasks.getTask())
                {
                    backDown = 5;
                }
                if (backDown <30)
                {
                    backDown++;
                }
            }

        }
    }
}
