using System;
using System.Collections;
using System.IO;
using System.Collections.Generic;
using System.Threading;

namespace hashtopolis
{
    class taskClass
    {

        hashcatClass hcClass = new hashcatClass();

        private string attackcmd;
        private string cmdpars;
        private Boolean stipPath;
        private string actualHLpath;
        private int benchTime, hashlistID, taskID, statusTimer, benchMethod, crackerId;
        private ArrayList files;
        private string hashlistAlias = "#HL#";

        private string prefixServerdl = "";
    
        private long chunkNo, skip, length;
        private string filepath, hashpath, appPath, zapPath, tasksPath;

        public Boolean debugFlag { get; set; }
        public _7zClass sevenZip { get; set; }
        public registerClass client { get; set; }
        public Boolean legacy { get; set; }
        private int offset = 0;

        public void setOffset()
        {
            if (!legacy)
            {
                offset = 1;
                Console.WriteLine("Using new STATUS codes");
            }
            else
            {
                Console.WriteLine("Using legacy STATUS codes");
            }
        }


        private List<string> primaryCracked; //Stores the cracked hashes as they come
        private object packetLock = new object(); //Lock to prevent the packetList from being edited as it's passed between the periodicUpload thread and the stdOut reader in hashcatClass

        public void setDirs(string fpath)
        {
            appPath = fpath;
            filepath = Path.Combine(fpath, "files");
            hashpath = Path.Combine(fpath, "hashlists");
            zapPath = Path.Combine(fpath, "hashlists", "zaps");
            tasksPath = Path.Combine(fpath, "tasks");
            prefixServerdl = client.connectURL.Substring(0, client.connectURL.IndexOf("/api/")) + "/";

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
            public int taskId { get; set; }
            public string file { get; set; }
        }


        private class chunkProps
        {
            public string action = "getChunk";
            public string token { get; set; }
            public int taskId { get; set; }
        }

        private class hashlistProps
        {
            public string action = "getHashlist";
            public string token { get; set; }
            public int hashlistId { get; set; }
        }

        private class keyspaceProps
        {
            public string action = "sendKeyspace";
            public string token { get; set; }
            public int taskId { get; set; }
            public long keyspace { get; set; }
        }

        private class benchProps
        {
            public string action = "sendBenchmark";
            public string token { get; set; }
            public int taskId { get; set; }
            public string type { get; set; }
            public string result { get; set; }
        }

        private class errorProps
        {
            public string action = "clientError";
            public string token { get; set; }
            public int taskId { get; set; }
            public string message { get; set; }
        }

        private class solveProps
        {
            public string action = "sendProgress";
            public string token { get; set; }
            public long chunkId { get; set; }
            public double keyspaceProgress { get; set; }
            public double relativeProgress { get; set; }
            //public double total { get; set; }
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
                token = client.tokenID,
                hashlistId = inTask
            };
            jsonClass jsC = new jsonClass { debugFlag = debugFlag, connectURL = client.connectURL };
            string jsonString = jsC.toJson(hProps);
            string ret = jsC.jsonSend(jsonString,300); //300 second timeout

            if (jsC.isJsonSuccess(ret))
            {
               
                getURLtoFile(jsC.getRetVar(ret, "url"), actualHLpath);
            }
             
            
            /*
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
            */

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
                return speed.ToString("F") + "H/s";
            }
            else if (count == 1)
            {
                return speed.ToString("F") + "KH/s";
            }
            else if (count == 2)
            {
                return speed.ToString("F") + "MH/s";
            }
            else if (count == 3)
            {
                return speed.ToString("F") + "GH/s";
            }
            else if (count == 4)
            {
                return speed.ToString("F") + "TH/s";
            }
            return speed.ToString("F");
        }

    
        //This runs as an independant thread and uploads the STATUS generated from the hcAttack
        //This thread is run on a dynamic timer based on the size of the queue and will range from a base 2500ms down to 200ms
        //There is very little discruption to the attack as a very quick lock/unlock is performed on the packet list to pop the job off the queue
        public void threadPeriodicUpdate(ref List<Packets> uploadPackets, ref object objPacketlock)
        {
            System.Globalization.CultureInfo customCulture = (System.Globalization.CultureInfo)System.Threading.Thread.CurrentThread.CurrentCulture.Clone();
            customCulture.NumberFormat.NumberDecimalSeparator = ".";
            System.Threading.Thread.CurrentThread.CurrentCulture = customCulture;

            jsonClass jsC = new jsonClass {debugFlag = debugFlag,  connectURL = client.connectURL };//Initis the json class
            solveProps sProps = new solveProps(); //Init the properties to build our json string
            List<string> receivedZaps = new List<string> { }; //List to store incoming zaps for writing
            string ret =""; //Return string from json post
            string jsonString ="";
            string zapfilePath = zapPath + hashlistID.ToString();
            long zapCount = 0;
            List<string> batchList = new List<string> { };
            double chunkPercent = 0;
            double chunkStart = 0;
            Boolean run = true;
            List<Packets> singlePacket  = new List<Packets> { };
            int sleepTime = 2500;
            long ulQueue = 0;
            hcClass.debugFlag = debugFlag;
            Boolean firstRun = true;
            
            string oPath = Path.Combine(tasksPath, taskID + "_" + chunkNo + ".txt"); // Path to write th -o file

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
                        sleepTime = 5000; //Decrese the time we process the queue
                    }
                    firstRun = false;
                }

                if (firstRun == true) //This is a work around to send a server a dummy stat to prevent timeouts on the initial start
                {

                    sProps.token = client.tokenID;
                    sProps.chunkId = chunkNo;
                    sProps.keyspaceProgress = skip;

                    sProps.relativeProgress = 0;

                    sProps.speed = 0;
                    sProps.state = 3; //Can't find the status code list lets try 3
                    sProps.cracks = new List<string>();
                    
                    jsonString = jsC.toJson(sProps);
                    ret = jsC.jsonSend(jsonString);

                    if (!jsC.isJsonSuccess(ret)) //If we received error, eg task was removed just break
                    {
                        break;
                    }
                }

                if (singlePacket.Count == 0)
                {
                    firstRun = false;
                    continue;
                }

                try
                {
                    {
                        //Special override as there is a possible race condition in HC, where STATUS4 doesn't give 100%
                        if (singlePacket[0].statusPackets["STATUS"] == 4 + offset)
                        {
                            singlePacket[0].statusPackets["PROGRESS1"] = singlePacket[0].statusPackets["PROGRESS2"];
                        }

                        sProps.token = client.tokenID;
                        sProps.chunkId = chunkNo;
                        sProps.keyspaceProgress = singlePacket[0].statusPackets["CURKU"];


                        chunkStart = Math.Floor(singlePacket[0].statusPackets["PROGRESS2"]) / (skip + length) * skip;
                        chunkPercent = Math.Round((Convert.ToDouble(singlePacket[0].statusPackets["PROGRESS1"]) - chunkStart) / Convert.ToDouble(singlePacket[0].statusPackets["PROGRESS2"] - chunkStart), 4) * 10000;

                        sProps.relativeProgress = chunkPercent;

                        //sProps.total = singlePacket[0].statusPackets["PROGRESS2"];
                        sProps.speed = singlePacket[0].statusPackets["SPEED_TOTAL"];
                        sProps.state = singlePacket[0].statusPackets["STATUS"] - offset; //Client-side workaround for old STATUS on server

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

                                if (!jsC.isJsonSuccess(ret)) //If we received error, eg task was removed just break
                                {
                                    break;
                                }
                            }
                                    
                        }
                        else
                        {
                            if (stipPath == true)
                            {
                                for (int i =0; i<= singlePacket[0].crackedPackets.Count-1; i++)
                                {
                                    singlePacket[0].crackedPackets[i] = singlePacket[0].crackedPackets[i].Replace(actualHLpath + ":", "");
                                }
                            }
                            sProps.cracks = singlePacket[0].crackedPackets;

                            jsonString = jsC.toJson(sProps);
                            ret = jsC.jsonSend(jsonString);
                        }
                    }


                    if (jsC.isJsonSuccess(ret))
                    {

                        if (jsC.getRetVar(ret, "agent") == "stop") //Special command sent by server, possibly undocumented
                        {
                            hcClass.hcProc.CancelOutputRead();
                            hcClass.hcProc.CancelErrorRead();
                            hcClass.hcProc.Kill();
                            run = false;
                            Console.WriteLine("Server has instructed the client terminate the task via stop");
                        }


                        chunkPercent = chunkPercent / 100; //We already calculated with * 10000 earlier

                        receivedZaps = jsC.getRetList(ret, "zaps"); //Check whether the server sent out hashes to zap
                        if (receivedZaps.Count > 0)
                        {
                            zapCount++;
                            File.WriteAllLines(Path.Combine(zapfilePath,zapCount.ToString()), receivedZaps); //Write hashes for zapping
                            
                        }
                        Console.WriteLine("Progress:{0,7} | Speed:{1,-4} | Cracks:{2,-4} | Accepted:{3,-4} | Zapped:{4,-4} | Queue:{5,-2}", chunkPercent.ToString("F") + "%", speedCalc(singlePacket[0].statusPackets["SPEED_TOTAL"]), singlePacket[0].crackedPackets.Count, jsC.getRetVar(ret, "cracked"), receivedZaps.Count,ulQueue);
                        receivedZaps.Clear();


                    }


                    else //We received an error from the server, terminate the run
                    {
                        
                        string writeCracked = Path.Combine(hashpath, Path.GetFileName(hashlistID.ToString())) + ".cracked";
                        Console.WriteLine("Writing any cracks in queue to file " + writeCracked);
                        File.AppendAllLines(writeCracked, singlePacket[0].crackedPackets);
                        lock (objPacketlock)
                        {
                            if (uploadPackets.Count > 0)
                            {
                                for (int i = 0; i < uploadPackets.Count; i++)
                                {
                                    if (uploadPackets[i].crackedPackets.Count > 0)
                                    {
                                        File.AppendAllLines(writeCracked, uploadPackets[i].crackedPackets);
                                    }
                                }
                            }
                        }

                        run = false; //Potentially we can change this so keep submitting the rest of the cracked queue instead of terminating
                     
                        if (!hcClass.hcProc.HasExited)
                        {
                            hcClass.hcProc.CancelOutputRead();
                            hcClass.hcProc.CancelErrorRead();
                            hcClass.hcProc.Kill();
                            //The server would need to accept the chunk but return an error
                        }
                        break;
                    }


                    {
                        if (singlePacket[0].statusPackets["STATUS"] >= 4 + offset) //We are the last upload task
                        //if (singlePacket[0].statusPackets["STATUS"] >= 5) //Uncomment this line, and comment above line for upcoming HC > 3.6
                        {
                            Console.WriteLine("Finished processing chunk");
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
                }
                
      
            }

        }

        private  jsonClass jsC = new jsonClass { };

        public int getChunk(int inTask)
        {
            Console.WriteLine("Getting chunk...");
             chunkProps cProps = new chunkProps
            {
                action = "getChunk",
                token = client.tokenID,
                taskId = inTask
            };

            jsC.debugFlag = debugFlag;
            jsC.connectURL = client.connectURL;
            primaryCracked = new List<string> { };
            hcClass.debugFlag = debugFlag;

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

                        attackcmdMod = convertToRelative(attackcmdMod);

                        attackcmdMod += " --outfile-check-dir=\"" + zapPath + hashlistID.ToString() + "\" "; //Add the zap path to the commands

                        hcClass.setArgs(attackcmdMod); 

                        chunkNo = Convert.ToInt64(jsC.getRetVar(ret, "chunkId"));
                        skip = Convert.ToInt64(jsC.getRetVar(ret, "skip"));
                        length = Convert.ToInt64(jsC.getRetVar(ret, "length"));

                        List<Packets> uploadPackets = new List<Packets>();

                        hcClass.setDirs(appPath);
                        hcClass.setPassthrough(ref uploadPackets, ref packetLock, debugFlag); 

                        Thread thread = new Thread(() => threadPeriodicUpdate(ref uploadPackets, ref packetLock)); 
                        thread.Start(); //Start our thread to monitor the upload queue

                        //Start the monitor thread here
                       

                        hcClass.startAttack(chunkNo, taskID, skip, length, statusTimer, tasksPath); //Start the hashcat binary
                        thread.Join();
                      
                        return 1;

                    case "keyspace_required":
                        hcClass.setDirs(appPath);
                        attackcmdMod = " " + cmdpars + " "; //Reset the argument string
                        attackcmdMod += attackcmd.Replace(hashlistAlias, ""); //Remove out the #HL#

                        attackcmdMod = convertToRelative(attackcmdMod);

                        hcClass.setArgs(attackcmdMod);
                        long calcKeyspace = 0;

                        if (!hcClass.runKeyspace(ref calcKeyspace))
                        {
                            Console.WriteLine("Keyspace measuring was unsuccessful, check all files are present");
                            return 0;
                        }


                        if (calcKeyspace == 0)
                        {
                            errorProps eProps = new errorProps
                            {
                                token = client.tokenID,
                                taskId = taskID,
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
                                token = client.tokenID,
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
                        hcClass.setDirs(appPath);
                        attackcmdMod = " " + cmdpars + " "; //Reset the argument string
                        attackcmdMod += attackcmd.Replace(hashlistAlias, "\"" + actualHLpath + "\""); //Add the path to Hashlist

                        attackcmdMod = convertToRelative(attackcmdMod);

                        hcClass.setArgs(attackcmdMod);

                        Dictionary<string, double> collection = new Dictionary<string, double>(); //Holds all the returned benchmark values1

                        if(!hcClass.runBenchmark(benchMethod, benchTime, ref collection, legacy))
                        {
                            Console.WriteLine("Benchmark error, perhaps hashlist is empty");
                            errorProps eProps = new errorProps
                            {
                                token = client.tokenID,
                                taskId = taskID,
                                message = "Client received an invalid hashlist for benchmark"
                            };
                            jsonString = jsC.toJson(eProps);
                            ret = jsC.jsonSend(jsonString);

                            return 0;

                        }

                        benchProps bProps = new benchProps
                        {
                            token = client.tokenID,
                            taskId = taskID,
                        };

                        try
                        {
                            if (benchMethod == 1) //Old benchmark method using actual run
                            {
                                bProps.type = "run";
                                bProps.result = collection["PROGRESS_REJ"].ToString("0." + new string('#', 100));

                            }
                            else //New benchmark method using --speed param
                            {
                                bProps.type = "speed";
                                bProps.result = collection["LEFT_TOTAL"].ToString() + ":" + collection["RIGHT_TOTAL"].ToString();
                            }
                        }
                        catch
                        {
                            Console.WriteLine("Benchmark was unsuccessful, check all files are present");
                            return 0;
                        }



                        jsonString = jsC.toJson(bProps);
                        ret = jsC.jsonSend(jsonString);
                        if (!jsC.isJsonSuccess(ret))
                        {
                            Console.WriteLine("Server rejected benchmark");
                            Console.WriteLine("Check the hashlist was downloaded correctly");
                            return 0; 
                        }
                        return 3;

                    }    

            }
            return 0;
        }

        private string convertToRelative(string input)
        {
            string[] filename = input.Split(' '); //Split by spaces
            string final = "";


            foreach (var file in filename)
            {
                if (File.Exists("files\\" + file))
                {
                    final  += "..\\..\\files\\" + file + " ";
                }
                else
                {
                    final += file + " ";
                }
            }

            if (client.osID != 1)
            {
                final = final.Replace("\\", "/");
            }

            return final;

        }
        private Boolean getFile(string fileName)
        {
            FileProps get = new FileProps
            {
                action = "getFile",
                token = client.tokenID,
                taskId = taskID,
                file = fileName
            };

            jsonClass jsC = new jsonClass {  debugFlag = debugFlag, connectURL = client.connectURL };
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

        private Boolean getURLtoFile(string url, string dst)
        {
            {
                downloadClass dlHdl = new downloadClass();
                string dlFrom = Path.Combine(prefixServerdl, url);
                string dlTo = Path.Combine(filepath, dst);
                dlHdl.DownloadFile(dlFrom, dlTo);
                Console.WriteLine("Finished downloading file");
                //Check if file exists. check if return success
                if (File.Exists(dlTo))
                {
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
                action = "getTask",
                token = client.tokenID
            };

            jsonClass jsC = new jsonClass { debugFlag = debugFlag, connectURL = client.connectURL };
            string jsonString = jsC.toJson(get);
            string   ret = jsC.jsonSend(jsonString);

            if (jsC.isJsonSuccess(ret))
            {
                if (jsC.getRetVar(ret, "taskId") != null)
                {
                    taskID = Int32.Parse(jsC.getRetVar(ret, "taskId"));
                    attackcmd = (jsC.getRetVar(ret, "attackcmd"));
                    cmdpars = (jsC.getRetVar(ret, "cmdpars"));
                    hashlistID = Int32.Parse(jsC.getRetVar(ret, "hashlistId"));
                    benchTime = Int32.Parse(jsC.getRetVar(ret, "bench"));
                    crackerId = Int32.Parse(jsC.getRetVar(ret, "crackerId"));

                    Console.WriteLine("Server has assigned client with Task:{0}, Cracker:{2} and Hashlist:{1}",taskID,hashlistID,crackerId);
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
                    if (client.osID != 1)
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

                    //Check if we have the correct cracker if not we download

                    hashcatUpdateClass hcUpdater = new hashcatUpdateClass { debugFlag = debugFlag, client = client, AppPath = appPath, sevenZip = sevenZip, binaryVersionId = Int32.Parse(jsC.getRetVar(ret, "crackerId"))};
                    
                    //If the cracker did not successfully initliaze then throw error and report
                    if (!hcUpdater.updateCracker())
                    {
                        errorProps eProps = new errorProps
                        {
                            token = client.tokenID,
                            taskId = taskID,
                            message = "Client could not locate cracker"
                        };
                        jsonString = jsC.toJson(eProps);
                        ret = jsC.jsonSend(jsonString);
                        return false;
                    }

                    //The client may change per task, we need to update these after the update
                    hcClass.hcDirectory = client.crackerPath;
                    hcClass.hcBinary = client.crackerBinary;

                    gotChunk = getChunk(taskID);

                    while (gotChunk != 0)
                    {
                        gotChunk = getChunk(taskID);
                    }

                    return true;
                }
                else
                {
                    Console.WriteLine("No new task assigned to agent");
                }


            }


            return false;
        }
    }
}
