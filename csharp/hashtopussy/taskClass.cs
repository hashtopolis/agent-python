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
        private int hashlistID;
        private int statusTimer;
        private ArrayList files;
        
        private static string prefixServerdl = "https://alpha.hashes.org/src/";
        private static string hashlistAlias = "#HL#";
        public static char separator = ':';

        private long chunkNo;
        private long skip;
        private long length;

        private string filepath;
        private string hashpath;
        private string appPath;
        private string zapPath;
        private string tasksPath;

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
            zapPath = Path.Combine(fpath, "hashlists","zaps");
            tasksPath = Path.Combine(fpath, "tasks");

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

            string actualHLpath = Path.Combine(hashpath , Path.GetFileName(inTask.ToString()));
            if (!File.Exists(actualHLpath))
            {
                Console.WriteLine("Downloading hashlist for this task");
            }
            else
            {
                Console.WriteLine("Hashlist for this task already exists, skipping download");
                return true;
            }



            hashlistProps hProps = new hashlistProps
            {
                token = tokenID,
                hashlist = inTask
            };

            jsonClass jsC = new jsonClass();
            string jsonString = jsC.toJson(hProps);
            string ret = jsC.jsonSend(jsonString);

            //Check if is json string, a nasty workaround copies from the javaclient to detect whether the return string is json vs hl. Should probably use a proper detector
            if (ret[0] != '{' && ret[ret.Length-1] != '}')
            {
                File.WriteAllText(actualHLpath, ret);
                Directory.CreateDirectory(Path.Combine(hashpath, "zaps" + inTask.ToString()));
            }
            else
            {
                jsC.isJsonSuccess(ret);
                return false;
            }

            return true;
        }
       

        public void threadPeriodicUpdate(ref List<Packets> uploadPackets, ref object objPacketlock)
        {
            jsonClass jsC = new jsonClass();//Initis the json class
            solveProps sProps = new solveProps(); //Init the properties to build our json string
            List<string> receivedZaps = new List<string> { }; //List to store incoming zaps for writing
            string ret; //Return string from json post
            string jsonString ="";
            string zapfilePath = zapPath + hashlistID.ToString();
            long zapCount = 0;
            Boolean batchJob = false;
            List<string> batchList = new List<string> { };
            int lastPacketNum = 0;
            double chunkPercent = 0;
            double chunkStart = 0;
            Boolean run = true;
            while (run)
            {
                Thread.Sleep(2500); //Delay this thread for 2.5 seconds, if this falls behind it will batch the jobs
                lock (objPacketlock)
                {
                    if (uploadPackets.Count > 0)
                    {
                        try
                        {
                            if (uploadPackets.Count > 10)
                            {
                                batchJob = true;
                                foreach (Packets packets in uploadPackets)
                                {
                                    batchList.AddRange(packets.crackedPackets); //Add every-single crack from queue into single list
                                }
                                lastPacketNum = uploadPackets.Count - 1;
                                sProps.token = tokenID;
                                sProps.chunk = chunkNo;
                                sProps.keyspaceProgress = uploadPackets[lastPacketNum].statusPackets["CURKU"];
                                sProps.progress = uploadPackets[lastPacketNum].statusPackets["PROGRESS1"];
                                sProps.total = uploadPackets[lastPacketNum].statusPackets["PROGRESS2"];
                                sProps.speed = uploadPackets[lastPacketNum].statusPackets["SPEED_TOTAL"];
                                sProps.state = uploadPackets[lastPacketNum].statusPackets["STATUS"];
                                sProps.cracks = batchList;
                            }

                            else
                            {
                                Console.WriteLine("Upload queue {0}", uploadPackets.Count);


                                sProps.token = tokenID;
                                sProps.chunk = chunkNo;
                                sProps.keyspaceProgress = uploadPackets[0].statusPackets["CURKU"];
                                sProps.progress = uploadPackets[0].statusPackets["PROGRESS1"];
                                sProps.total = uploadPackets[0].statusPackets["PROGRESS2"];
                                sProps.speed = uploadPackets[0].statusPackets["SPEED_TOTAL"];
                                sProps.state = uploadPackets[0].statusPackets["STATUS"];
                                sProps.cracks = uploadPackets[0].crackedPackets;


                            }

                            jsonString = jsC.toJson(sProps);
                            Console.WriteLine(jsonString);

                            ret = jsC.jsonSend(jsonString);
                            if (jsC.isJsonSuccess(ret))
                            {

                                chunkStart = Math.Floor(uploadPackets[0].statusPackets["PROGRESS2"]) / (skip + length) * skip;
                                chunkPercent = Math.Round((Convert.ToDouble(uploadPackets[0].statusPackets["PROGRESS1"]) - chunkStart) / Convert.ToDouble(uploadPackets[0].statusPackets["PROGRESS2"] - chunkStart) ,4)* 100;

                                Console.WriteLine("Progress: {0}% Speed: {1}", chunkPercent, uploadPackets[0].statusPackets["SPEED_TOTAL"]);


                                if (uploadPackets[0].crackedPackets.Count != 0) //Give some info if cracks were submitted
                                {
                                    Console.WriteLine("Uploaded {0} cracks, server accepted {1}", uploadPackets[0].crackedPackets.Count, jsC.getRetVar(ret, "cracked"));
                                }

                                receivedZaps = jsC.getRetList(ret, "zaps"); //Check whether the server sent out hashes to zap
                                if (receivedZaps.Count > 0)
                                {
                                    zapCount++;
                                    File.WriteAllLines(zapfilePath + zapCount.ToString(), receivedZaps); //Write hashes for zapping
                                    Console.WriteLine("Zapped {0} hashes", receivedZaps.Count);
                                    receivedZaps.Clear();
                                }
                            }


                            else //We received an error from the server, terminate the run
                            {

                                if (!hcClass.hcProc.HasExited)
                                {
                                    hcClass.hcProc.CancelOutputRead();
                                    hcClass.hcProc.CancelErrorRead();
                                    hcClass.hcProc.Kill();
                                    run = false; //Potentially we can change this so keep submitting the rest of the cracked queue instead of terminating
                                    //The server would need to accept the chunk but return an error
                                }

                            }


                            if (batchJob == false)
                            {
                                if (uploadPackets[0].statusPackets["STATUS"] >= 4 && uploadPackets.Count == 1) //We are the last upload task
                                {
                                    Console.WriteLine("Finished last chunk");
                                    uploadPackets.Clear();
                                    run = false;
                                }
                                else
                                {
                                    uploadPackets.RemoveAt(0);
                                }
                                
                            }
                            else
                            {
                                if (uploadPackets[lastPacketNum].statusPackets["STATUS"] >= 4) //We are the last upload task
                                {
                                    Console.WriteLine("Finished last chunk");
                                    uploadPackets.Clear();
                                    run = false;
                                }
                                uploadPackets.Clear();
                            }

                        }
                        catch (Exception e)
                        {
                            Console.WriteLine(e.Message);

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
            }
        }

        private jsonClass jsC = new jsonClass { debugFlag = true };

        public int getChunk(int inTask)
        {
             chunkProps cProps = new chunkProps
            {
                action = "chunk",
                token = tokenID,
                taskId = inTask
            };

            
            primaryCracked = new List<string> { };

            string jsonString = jsC.toJson(cProps);
            string ret = jsC.jsonSend(jsonString);
            

            if (jsC.isJsonSuccess(ret))
            {
                string status = jsC.getRetVar(ret, "status");
                

                string argBuilder = attackcmd;
                string attackcmdMod = " " + cmdpars + " ";
                string actualHLpath = Path.Combine(hashpath, hashlistID.ToString());
                int benchMarkMethod = 1;
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
                        hcClass.setPassthrough(ref uploadPackets, ref packetLock, separator.ToString()); 

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

                        keyspaceProps kProps = new keyspaceProps
                        {
                            token = tokenID,
                            taskId = taskID,
                            keyspace = calcKeyspace
                        };


                        jsonString = jsC.toJson(kProps);
                        ret = jsC.jsonSend(jsonString);

                        return 2;

                    case "fully_dispatched":
                        return 0;

                    case "benchmark":
                        hcClass.setDirs(appPath, osID);
                        attackcmdMod = " " + cmdpars + " "; //Reset the argument string
                        attackcmdMod += attackcmd.Replace(hashlistAlias, "\"" + actualHLpath + "\""); //Add the path to Hashlist
                        hcClass.setArgs(attackcmdMod);

                        Dictionary<string, double> collection = new Dictionary<string, double>(); //Holds all the returned benchmark values1

                        hcClass.runBenchmark(1, benchTime, ref collection);

                        benchProps bProps = new benchProps
                        {
                            token = tokenID,
                            taskId = taskID,
                        };

                        if (benchMarkMethod == 1) //Old benchmark method using actual run
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

            jsonClass jsC = new jsonClass();
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
                    Console.WriteLine("Finished DL");
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

            jsonClass jsC = new jsonClass();
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
                    statusTimer = Int32.Parse(jsC.getRetVar(ret, "statustimer"));
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
