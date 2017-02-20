using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;

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

        public static string AppPath;

        static void initDirs()
        {
            string filesDir = Path.Combine(AppPath,"files");
            if (!Directory.Exists(filesDir))
            {
                Console.WriteLine("Creating files directory");
                Directory.CreateDirectory(filesDir);
            }
            string hashlistDir = Path.Combine(AppPath, "hashlists");
            if (!Directory.Exists(hashlistDir))
            {
                Console.WriteLine("Creating hashlist directory");
                Directory.CreateDirectory(hashlistDir);
            }

            string taskDir = Path.Combine(AppPath, "tasks");
            if (!Directory.Exists(taskDir))
            {
                Console.WriteLine("Creating tasks directory");
                Directory.CreateDirectory(taskDir);
            }

        }

        private static string urlPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"URL");
        private static string serverURL = "";

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

        static void Main(string[] args)
        {

            string AppVersion = "0.2";
            jsonClass testConnect = new jsonClass { debugFlag = true, };
            testProp tProp = new testProp();
            while (!loadURL())
            {
                Console.WriteLine("Could not locate server URL, please enter URL:");
                string url = Console.ReadLine();
                if (!url.StartsWith("http"))
                {
                    url = "https://" + url;
                }

                testConnect.connectURL = url;
                Console.WriteLine(url);
                string jsonString = testConnect.toJson(tProp);
                string ret = testConnect.jsonSendOnce(jsonString);
                if (testConnect.isJsonSuccess(ret))
                {
                    File.WriteAllText(urlPath, url);
                }
                
                
            }

            Console.WriteLine("Client Version " + AppVersion);
            AppPath = AppDomain.CurrentDomain.BaseDirectory;
            updateClass updater = new updateClass
            {
                htpVersion = AppVersion,
                parentPath = AppPath,
                arguments = args,
                connectURL = serverURL

            };

            updater.runUpdate();

            initDirs();

            registerClass client = new registerClass { connectURL = serverURL };
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
                appPath = AppPath
            };

            zipper.init7z();

            taskClass tasks = new taskClass
            {
                tokenID = client.tokenID,
                osID = client.osID,
                sevenZip = zipper,
                connectURL = serverURL

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
