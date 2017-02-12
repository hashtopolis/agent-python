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

        static void Main(string[] args)
        {

           
            AppPath = AppDomain.CurrentDomain.BaseDirectory;
            updateClass updater = new updateClass();
            updater.setParentPath (AppPath);
            for (int i = 0; i < args.Length; i++)
            {
                if (args[i] != "debug")
                {
                    updater.setParent(args[i]);
                }
            }

            updater.runUpdate();


            initDirs();

            registerClass client = new registerClass();
            client.setPath( AppPath);
            if (client.loginAgent())
            {
                Console.WriteLine("Logged in to server");
            }

            downloadClass dlHdl = new downloadClass();
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
                sevenZip = zipper
            };
                
            tasks.setDirs(AppPath);

            while(true) //Keep waiting for 5 seconds and checking for tasks
            {
                Thread.Sleep(5000);
                tasks.getTask();
            }


        }
    }
}
