using System;
using System.Collections;
using System.IO;
using System.Collections.Generic;
using System.Threading;

namespace hashtopussy
{
    class taskClass
    {

        hashcatClass hcClass = new hashcatClass();

        private int taskID;
        private string attackcmd;
        private string cmdpars;
        private int benchTime;
        private Boolean stipPath;
        private string actualHLpath;
        private int hashlistID;
        private int statusTimer;
        private int benchMethod;
        private ArrayList files;
        private string hashlistAlias = "#HL#";


        private string prefixServerdl = "";
        public static char separator = ':';

        private long chunkNo;
        private long skip;
        private long length;

        private string filepath;
        private string hashpath;
        private string appPath;
        private string zapPath;
        private string tasksPath;

        public string connectURL { get; set; }
        public Boolean debugFlag { get; set; }
        public string tokenID { get; set; }
        public int osID { get; set; }
        public _7zClass sevenZip { get; set; }

        private List<string> primaryCracked; //Stores the cracked hashes as they come
        private object packetLock = new object(); //Lock to prevent the packetList from being edited as it's passed between the periodicUpload thread and the stdOut reader in hashcatClass


        public void setDirs(string fpath)
        {
            appPath = fpath;
            filepath = Path.Combine(fpath, "files");
            hashpath = Path.Combine(fpath, "hashlists");
            zapPath = Path.Combine(fpath, "hashlists", "zaps");
            tasksPath = Path.Combine(fpath, "tasks");
            prefixServerdl = connectURL.Substring(0, connectURL.IndexOf("/api/")) + "/";

        }

        private class Task
        {
            public string action { get; set; }
            public string token { get; set; }
        }

        private class FileProps
        {
            public string action { get; set; }
            public string token { get; set; }
            public int task { get; set; }
            public string file { get; set; }
        }


        private class chunkProps
        {
            public string action = "chunks";
            public string token { get; set; }
            public int taskId { get; set; }
        }

        private class hashlistProps
        {
            public string action = "hashes";
            public string token { get; set; }
            public int hashlist { get; set; }
        }

        private class keyspaceProps
        {
            public string action = "keyspace";
            public string token { get; set; }
            public int taskId { get; set; }
            public long keyspace { get; set; }
        }

        private class benchProps
        {
            public string action = "bench";
            public string token { get; set; }
            public int taskId { get; set; }
            public string type { get; set; }
            public string result { get; set; }
        }

        private class errorProps
        {
            public string action = "error";
            public string token { get; set; }
            public int task { get; set; }
            public string message { get; set; }
        }

        private class solveProps
        {
            public string action = "solve";
            public string token { get; set; }
            public long chunk { get; set; }
            public double keyspaceProgress { get; set; }
            public double progress { get; set; }
            public double total { get; set; }
            public double speed { get; set; }
            public double state { get; set; }
            public List<string> cracks { get; set; }
        }

        public Boolean getHashes(int inTask)
        {

             actualHLpath = Path.Combine(hashpath, Path.GetFileName(inTask.ToString()));

            Console.WriteLine("Downloading hashlist for this task, please wait...");

            hashlistProps hProps = new hashlistProps
            {
                token = tokenID,
                hashlist = inTask
            };

            jsonClass jsC = new jsonClass { debugFlag = debugFlag, connectURL = connectURL };
            string jsonString = jsC.toJson(hProps);
            string ret = jsC.jsonSend(jsonString);

            //Check if is json string, a nasty workaround copies from the javaclient to detect whether the return string is json vs hl. Should probably use a proper detector
            if (ret[0] != '{' && ret[ret.Length - 1] != '}')
            {
                File.WriteAllText(actualHLpath, ret);
                Directory.CreateDirectory(Path.Combine(hashpath, "zaps" + inTask.ToString()));
            }
            else
            {
                if (jsC.isJsonSuccess(ret))
                {
                    string b64data = jsC.getRetVar(ret,"data");
                    byte[] binArray = System.Convert.FromBase64String(b64data);
                    File.WriteAllBytes(actualHLpath, binArray);
                    stipPath = true; //Strip path for all HL recieved binary hashlsits
            
                }
                else
                {
                    return false;
                }
                
            }

            return true;
        }

        public string speedCalc(double speed)
        {
            int count = 0;
            while (speed > 1000)
            {
                speed = speed / 1000;
                count++;
            }

            speed = Math.Round(speed, 2);

            if (count == 0)
            {
                return speed.ToString() + "KH/s";
            }
            else if (count == 1)
            {
                return speed.ToString() + "MH/s";
            }
            else if (count == 2)
            {
                return speed.ToString() + "GH/s";
            }
            else if (count == 3)
            {
                return speed.ToString() + "TH/s";
            }

            return speed.ToString();
        }

    
        //This runs as an independant thread and uploads the STATUS generated from the hcAttack
        //This thread is run on a dynamic timer based on the size of the queue and will range from a base 2500ms down to 200ms
        //There is very little discruption to the attack as a very quick lock/unlock is performed on the packet list to pop the job off the queue
        public void threadPeriodicUpdate(ref List<Packets> uploadPackets, ref object objPacketlock)
        {
            System.Globalization.CultureInfo customCulture = (System.Globalization.CultureInfo)System.Threading.Thread.CurrentThread.CurrentCulture.Clone();
            customCulture.NumberFormat.NumberDecimalSeparator = ".";
            System.Threading.Thread.CurrentThread.CurrentCulture = customCulture;

            jsonClass jsC = new jsonClass {debugFlag = debugFlag,  connectURL = connectURL };//Initis the json class
            solveProps sProps = new solveProps(); //Init the properties to build our json string
            List<string> receivedZaps = new List<string> { }; //List to store incoming zaps for writing
            string ret =""; //Return string from json post
            string jsonString ="";
            string zapfilePath = zapPath + hashlistID.ToString();
            long zapCount = 0;
            List<string> batchList = new List<string> { };
            int lastPacketNum = 0;
            double chunkPercent = 0;
            double chunkStart = 0;
            Boolean run = true;
            List<Packets> singlePacket  = new List<Packets> { };
            int sleepTime = 2500;
            long ulQueue = 0;

            while (run)
            {
                Thread.Sleep(sleepTime); //Delay this thread for 2.5 seconds, if this falls behind it will batch the jobs
                lock (objPacketlock)
                {
                    if (uploadPackets.Count > 0)
                    {
                        singlePacket.Add(uploadPackets[0]);
                        ulQueue = uploadPackets.Count;
                        uploadPackets.RemoveAt(0);
                        if (uploadPackets.Count > 3)

                        sleepTime = 200; //Decrese the time we process the queue
                    }
                    else
                    {
                        sleepTime = 2500; //Decrese the time we process the queue
                    }
                }


                if (singlePacket.Count == 0)
                {
                    continue;
                }

                try
                {
                    { 
                        sProps.token = tokenID;
                        sProps.chunk = chunkNo;
                        sProps.keyspaceProgress = singlePacket[0].statusPackets["CURKU"];
                        sProps.progress = singlePacket[0].statusPackets["PROGRESS1"];
                        sProps.total = singlePacket[0].statusPackets["PROGRESS2"];
                        sProps.speed = singlePacket[0].statusPackets["SPEED_TOTAL"];
                        sProps.state = singlePacket[0].statusPackets["STATUS"];

                        if (singlePacket[0].crackedPackets.Count > 200)
                        {
                            int max = 200;

                            //Process the requests in batches of 1000
                            while (singlePacket[0].crackedPackets.Count != 0)
                            {
                                List<string> subChunk = new List<string>(singlePacket[0].crackedPackets.GetRange(0, max));
                                singlePacket[0].crackedPackets.RemoveRange(0, max);
                                if (singlePacket[0].crackedPackets.Count < max)
                                {
                                    max = singlePacket[0].crackedPackets.Count;
                                }

                                if (stipPath == true)
                                {
                                    for (int i = 0; i <= subChunk.Count-1; i++)
                                    {
                                        subChunk[i] = subChunk[i].Replace(actualHLpath + ":", "");
                                    }
                                }

                                sProps.cracks = subChunk;
                                jsonString = jsC.toJson(sProps);
                                ret = jsC.jsonSend(jsonString);
                                Console.WriteLine(ret);
                            }
                                    
                        }
                        else
                        {
                            if (stipPath == true)
                            {
                                for (int i =0; i<= singlePacket[0].crackedPackets.Count-1; i++)
                                {
                                    singlePacket[i].crackedPackets[i] = singlePacket[0].crackedPackets[i].Replace(actualHLpath + ":", "");
                                }
                            }
                            sProps.cracks = singlePacket[0].crackedPackets;

                            jsonString = jsC.toJson(sProps);
                            ret = jsC.jsonSend(jsonString);
                        }
                    }


                    if (jsC.isJsonSuccess(ret))
                    {

                        chunkStart = Math.Floor(singlePacket[0].statusPackets["PROGRESS2"]) / (skip + length) * skip;
                        chunkPercent = Math.Round((Convert.ToDouble(singlePacket[0].statusPackets["PROGRESS1"]) - chunkStart) / Convert.ToDouble(singlePacket[0].statusPackets["PROGRESS2"] - chunkStart) ,4)* 100;


                        receivedZaps = jsC.getRetList(ret, "zaps"); //Check whether the server sent out hashes to zap
                        if (receivedZaps.Count > 0)
                        {
                            zapCount++;
                            File.WriteAllLines(zapfilePath + zapCount.ToString(), receivedZaps); //Write hashes for zapping
                            receivedZaps.Clear();
                        }
                        Console.WriteLine("Progress:{0}% | Speed:{1} | Cracks:{2} | Accepted:{3} | Zapped:{4} | Queue:{5}", chunkPercent, speedCalc(singlePacket[0].statusPackets["SPEED_TOTAL"]), singlePacket[0].crackedPackets.Count, jsC.getRetVar(ret, "cracked"), receivedZaps.Count,ulQueue);

                    }


                    else //We received an error from the server, terminate the run
                    {

                        if (!hcClass.hcProc.HasExited)
                        {
                            Console.WriteLine("Error received");
                            hcClass.hcProc.CancelOutputRead();
                            hcClass.hcProc.CancelErrorRead();
                            hcClass.hcProc.Kill();
                            run = false; //Potentially we can change this so keep submitting the rest of the cracked queue instead of terminating
                            //The server would need to accept the chunk but return an error
                        }

                    }



                    {
                        if (singlePacket[lastPacketNum].statusPackets["STATUS"] >= 4) //We are the last upload task
                        {
                            Console.WriteLine("Finished last chunk");
                            singlePacket.Clear();
                            run = false;
                        }
                        else
                        {
                            singlePacket.RemoveAt(0);
                        }
                        
                    }


                }
                catch (Exception e)
                {
                    Console.WriteLine(e.Message);
                    Console.WriteLine("Error processing packet for upload");
                    /*
                    hcClass.hcProc.CancelOutputRead();
                    hcClass.hcProc.CancelErrorRead();
                    if (!hcClass.hcProc.HasExited)
                    {
                        hcClass.hcProc.Kill();
                    }
                    */

                    continue;
                            
                }

            }
   
        }

        private  jsonClass jsC = new jsonClass { };

        public int getChunk(int inTask)
        {
             chunkProps cProps = new chunkProps
            {
                action = "chunk",
                token = tokenID,
                taskId = inTask
            };

            jsC.debugFlag = debugFlag;
            jsC.connectURL = connectURL;
            primaryCracked = new List<string> { };

            string jsonString = jsC.toJson(cProps);
            string ret = jsC.jsonSend(jsonString);
            

            if (jsC.isJsonSuccess(ret))
            {
                string status = jsC.getRetVar(ret, "status");
                

                string argBuilder = attackcmd;
                string attackcmdMod = " " + cmdpars + " ";
                string actualHLpath = Path.Combine(hashpath, hashlistID.ToString());
                switch (status)
                {
                    case "OK":
                        attackcmdMod = " " + cmdpars + " "; //Reset the argument string
                        attackcmdMod += attackcmd.Replace(hashlistAlias, "\"" + actualHLpath + "\" "); //Add the path to Hashlist
                        attackcmdMod += " --outfile-check-dir=\"" + zapPath + hashlistID.ToString() + "\" "; //Add the zap path to the commands

                        hcClass.setArgs(attackcmdMod);


                        chunkNo = Convert.ToInt64(jsC.getRetVar(ret, "chunk"));
                        skip = Convert.ToInt64(jsC.getRetVar(ret, "skip"));
                        length = Convert.ToInt64(jsC.getRetVar(ret, "length"));

                        List<Packets> uploadPackets = new List<Packets>();

                        hcClass.setDirs(appPath,osID);
                        hcClass.setPassthrough(ref uploadPackets, ref packetLock, separator.ToString(),debugFlag); 

                        Thread thread = new Thread(() => threadPeriodicUpdate(ref uploadPackets, ref packetLock)); 
                        thread.Start(); //Start our thread to monitor the upload queue

                        hcClass.startAttack(0, skip, length, separator.ToString(), statusTimer, tasksPath); //Start the hashcat binary
                        thread.Join();
                      
                        return 1;

                    case "keyspace_required":
                        hcClass.setDirs(appPath,osID);
                        attackcmdMod = " " + cmdpars + " "; //Reset the argument string
                        attackcmdMod += attackcmd.Replace(hashlistAlias, ""); //Remove out the #HL#
                        hcClass.setArgs(attackcmdMod);
                        long calcKeyspace = 0;

                        hcClass.runKeyspace(ref calcKeyspace);


                        if (calcKeyspace == 0)
                        {
                            errorProps eProps = new errorProps
                            {
                                token = tokenID,
                                task = taskID,
                                message = "Invalid keyspace, keyspace probably too small for this hashtype"
                            };
                            jsonString = jsC.toJson(eProps);
                            ret = jsC.jsonSend(jsonString);
                            return 0;
                        }
                        else
                        {
                            keyspaceProps kProps = new keyspaceProps
                            {
                                token = tokenID,
                                taskId = taskID,
                                keyspace = calcKeyspace
                            };
                            jsonString = jsC.toJson(kProps);
                            ret = jsC.jsonSend(jsonString);

                        }

                        return 2;

                    case "fully_dispatched":
                        return 0;

                    case "benchmark":
                        hcClass.setDirs(appPath, osID);
                        attackcmdMod = " " + cmdpars + " "; //Reset the argument string
                        attackcmdMod += attackcmd.Replace(hashlistAlias, "\"" + actualHLpath + "\""); //Add the path to Hashlist
                        hcClass.setArgs(attackcmdMod);

                        Dictionary<string, double> collection = new Dictionary<string, double>(); //Holds all the returned benchmark values1

                        hcClass.runBenchmark(benchMethod, benchTime, ref collection);

                        benchProps bProps = new benchProps
                        {
                            token = tokenID,
                            taskId = taskID,
                        };

                        if (benchMethod == 1) //Old benchmark method using actual run
                        {
                            bProps.type = "run";
                            bProps.result = collection["PROGRESS_DIV"].ToString("0." + new string('#', 100));
                        }
                        else //New benchmark method using --speed param
                        {
                            bProps.type = "speed"; 
                            bProps.result = collection["LEFT_TOTAL"].ToString() + ":" + collection["RIGHT_TOTAL"].ToString();
                        }


                        jsonString = jsC.toJson(bProps);
                        ret = jsC.jsonSend(jsonString);
                        if (!jsC.isJsonSuccess(ret))
                        {
                            Console.WriteLine("Server rejected benchmark");
                            Console.WriteLine("Check the hashlist was downloaded correctly");
                            Environment.Exit(1);
                            Console.WriteLine("Terminating task due to bad benchmark");
                        }
                        return 3;
                    }    

            }
            return 0;
        }

        private Boolean getFile(string fileName)
        {
            FileProps get = new FileProps
            {
                action = "file",
                token = tokenID,
                task = taskID,
                file = fileName
            };

            jsonClass jsC = new jsonClass {  debugFlag = debugFlag, connectURL = connectURL };
            string jsonString = jsC.toJson(get);
            string ret = jsC.jsonSend(jsonString);

            if (jsC.isJsonSuccess(ret))
            {
                string fileDl = jsC.getRetVar(ret, "url");
                {
                    downloadClass dlHdl = new downloadClass();
                    string dlFrom = Path.Combine(prefixServerdl, jsC.getRetVar(ret, "url"));
                    string dlTo = Path.Combine(filepath,fileName);
                    dlHdl.DownloadFile(dlFrom, dlTo);
                    Console.WriteLine("Finished downloading file");
                    //Check if file exists. check if return success
                    return true;
                }
                
            }
            return false;
        }


        private Int64 fileSize(string filePath)
        {
            Int64 fSize = new FileInfo(Path.Combine(hashpath , Path.GetFileName(hashlistID.ToString()))).Length;
            return fSize;
        }


        public Boolean getTask()
        {

            Console.WriteLine("Getting task");
            Task get = new Task
            {
                action = "task",
                token = tokenID
            };

            jsonClass jsC = new jsonClass { debugFlag = debugFlag, connectURL = connectURL };
            string jsonString = jsC.toJson(get);
             string   ret = jsC.jsonSend(jsonString);



            if (jsC.isJsonSuccess(ret))
            {
                if (jsC.getRetVar(ret, "task") != "NONE")
                {
                    taskID = Int32.Parse(jsC.getRetVar(ret, "task"));
                    attackcmd = (jsC.getRetVar(ret, "attackcmd"));
                    cmdpars = (jsC.getRetVar(ret, "cmdpars"));
                    hashlistID = Int32.Parse(jsC.getRetVar(ret, "hashlist"));
                    benchTime = Int32.Parse(jsC.getRetVar(ret, "bench"));
                    if (jsC.getRetVar(ret, "benchType") == "run")
                    {
                        benchMethod = 1;
                    }
                    else
                    {
                        benchMethod = 2;
                    }
                    statusTimer = Int32.Parse(jsC.getRetVar(ret, "statustimer"));
                    hashlistAlias = jsC.getRetVar(ret, "hashlistAlias");
                    files = jsC.getRetArray(ret, "files");
                    int gotChunk = 1;

                    foreach (string fileItem in files)
                    {
                        string actualFile = Path.Combine(filepath, fileItem);
                        if (!File.Exists(actualFile))
                        {
                            getFile(fileItem);
                           
                            if (fileItem.ToLower().EndsWith(".7z"))
                            {            
                                if (sevenZip.xtract(actualFile, filepath))
                                {
                                    File.WriteAllText(actualFile, "UNPACKED");
                                }
                                else
                                {
                                    return false;
                                }
                            }
                        }
                    }

                    //Convert implied relative paths to absolute paths only applies to Mac OSX / Linux
                    //We, break up the attack command by space and check whether the file for the full path exists, we it does we replace
                    //Could potentially cause issues if the file names are attack numbers eg 1 2 3 4 5 6 7
                    //File names cannot contain spaces
                    //Altnerative method is to perform find replace on the attackcmd based on the files array
                    if (osID != 1)
                    {
                        string[] explode = new string[] { };
                        explode = attackcmd.Split(' ');

                        for (int i = 0; i<files.Count; i++)
                        {
                            string absolutePath = Path.Combine(filepath, files[i].ToString());
                            string match = " " + files[i].ToString(); //Prefix a space for better matching
                            string replace = " \"" + absolutePath + "\"";
                            if (File.Exists(absolutePath))
                            {
                                attackcmd = attackcmd.Replace(match, replace);
                            }
                        }

                        /*
                        for (int i = 0; i<explode.Length; i++)
                        {
                            if (files.Contains(explode[i]));
                            {
                                string absolutePath = Path.Combine(filepath, explode[i]);
                                if (File.Exists(absolutePath))
                                {
                                    explode[i] = absolutePath;
                                }
                            } 
                        }
                        attackcmd = String.Join(" ", explode);
                        */
                    }

                    if (getHashes(hashlistID) == false)
                    {
                        return false;
                    }
                    

                    if (fileSize(Path.Combine(hashpath, Path.GetFileName(hashlistID.ToString()))) == 0)
                    {
                        Console.WriteLine("Hashlist is 0 bytes");
                        return false;
                    }
                    gotChunk = getChunk(taskID);

                    while (gotChunk != 0)
                    {
                        gotChunk = getChunk(taskID);
                    }

                    return true;
                }


            }


            return false;
        }
    }
}
