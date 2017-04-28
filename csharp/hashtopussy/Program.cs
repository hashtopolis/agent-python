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


                if (Console.LargestWindowWidth > 94 && Console.LargestWindowHeight > 24)
                {
                    Console.SetWindowSize(95, 25);
                }
                
     
            
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

            string AppVersion = "0.43.16";
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

                hashcatUpdateClass hcUpdater = new hashcatUpdateClass {debugFlag = DebugMode, client = client, AppPath = AppPath,sevenZip = zipper};

                if (hcUpdater.updateHashcat())
                {
                    hashcatClass hcClass = new hashcatClass { };
                    hcClass.setDirs(AppPath, client.osID);
                    string hcVersion = hcClass.getVersion2();
                    Console.WriteLine("Hashcat version {0} found", hcVersion);
                }
                else
                {
                    Console.WriteLine("Could not locate hashcat binary");
                    Console.WriteLine("You can manually download and extract hashcat");
                    Console.WriteLine("Client will now terminate");
                    {
                        Environment.Exit(0);
                    }
                }

            }

            taskClass tasks = new taskClass
            {
                sevenZip = zipper,
                debugFlag = DebugMode,
                client = client
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
