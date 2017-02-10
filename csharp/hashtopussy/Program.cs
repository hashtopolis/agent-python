using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.IO;
using System.Net;
using System.Web.Script.Serialization;
using System.Dynamic;
using System.Management;
using System.Collections;
using System.Collections.Specialized;
using System.Diagnostics;
using System.Text.RegularExpressions;
using System.Threading;

namespace hashtopussy
{

    public class Account
    {
        public string Email { get; set; }
        public bool Active { get; set; }
        public DateTime CreatedDate { get; set; }
        public IList<string> Roles { get; set; }
    }

    public struct Packets
    {
        public Dictionary<string, double> statusPackets;
        public List<string> crackedPackets;
        public bool stop;
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
            //Directory.SetCurrentDirectory(AppPath);
            //Console.Write(AppPath);
            updateClass updateHdl = new updateClass();
            updateHdl.setParentPath (AppPath);
            for (int i = 0; i < args.Length; i++)
            {
                if (args[i] != "debug")
                {
                    updateHdl.setParent(args[i]);
                }
            }

            updateHdl.runUpdate();


            initDirs();

            tokenClass tokenHdl = new tokenClass();
            tokenHdl.setPath( AppPath);
            if (tokenHdl.loginAgent())
            {
                Console.WriteLine("Logged in to server");
            }

            downloadClass dlHdl = new downloadClass();
            //Run code to self-update

            _7zClass zipper = new _7zClass();
            zipper.init7z(AppPath, 1, tokenHdl.retToken());


            taskClass tasks = new taskClass();
            tasks.setDirs(AppPath);
            tasks.setToken(tokenHdl.retToken());
            
            while(true) //Keep waiting for 5 seconds and checking for tasks
            {
                Thread.Sleep(5000);
                tasks.getTask();
            }


        }
    }
}
