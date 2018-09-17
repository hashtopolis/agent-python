using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Diagnostics;
using System.Text.RegularExpressions;
using System.Globalization;

namespace hashtopolis
{
    class hashcatClass : IDisposable
    {
        public Boolean debugFlag { get; set; }

        public List<string> hashlist = new List<string> { }; //New collection to store cracks
        public Process hcProc;

        private string workingDir = "";
        private string filesDir = "";
        private string hcDir = "hashcat";
        private string hcBin = "hashcat64.exe";
        public string hcDirectory { get; set; }
        public string hcBinary { get; set; }

        private string hcArgs = "";
 
        private object packetLock;
        private object crackedLock;
        private object statusLock;

        List<Packets> passedPackets;

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        protected virtual void Dispose(bool disposing)
        {
            if (disposing)
            {
                if (!hcProc.HasExited )
                {
                    hcProc.Kill();
                    hcProc.Dispose();
                }
            }
        }

        public void setPassthrough(ref List<Packets> refPacketlist, ref object objpacketLock, Boolean debugging)
        {
            passedPackets = refPacketlist;
            packetLock = objpacketLock;

            crackedLock = new object();
            statusLock = new object();
            debugFlag = debugging;

        }
         
        public void setArgs(string args)
        {
            
            hcArgs = args;
        }

        public void setDirs(string fpath)
        {
            hcDir = Path.Combine(fpath, hcDirectory);
            workingDir = Path.Combine(fpath, "tasks").TrimEnd();
            filesDir = Path.Combine(fpath, "files"," ").TrimEnd();

            hcBin = hcBinary;

        }

        public void runUpdate()
        {
            if (!Directory.Exists(hcDir))
            {
                //forceUpdate = true;
            }
        }



        private void parseStatus1(string line,ref  Dictionary<string, double> collection)
        {

            System.Globalization.CultureInfo customCulture = (System.Globalization.CultureInfo)System.Threading.Thread.CurrentThread.CurrentCulture.Clone();
            customCulture.NumberFormat.NumberDecimalSeparator = ".";
            System.Threading.Thread.CurrentThread.CurrentCulture = customCulture;

            //Console.WriteLine(line);

            string[] items = line.Split('\t');
            double speedData = 0;
            double countStep = 0;
            double execRuntime = 0;

            int max = items.Count();
            int i = 0;

            if (debugFlag)
            {
                Console.WriteLine(line);
            }
            

            while(i < max)
            {
                countStep = 0;
                switch (items[i])
                {
                    case "STATUS":
                        collection.Add("STATUS", Convert.ToInt64(items[i + 1]));
                        i =+ 1;
                        break;
                    case "SPEED":
                        while (items[i+1] != "EXEC_RUNTIME") //Due to multiple cards, perform micro-loop
                        {
                            collection.Add("SPEED" + countStep, Convert.ToDouble(items[i + 1]));
                            speedData += (Convert.ToDouble(items[i + 1]) * 1000) / Convert.ToDouble(items[i + 2]); //For hashcat 3.7 compatability
                            countStep++;
                            i += 2;
                        }
                        collection.Add("SPEED_TOTAL", speedData);
                        collection.Add("SPEED_COUNT", countStep);
                        break;
                    case "EXEC_RUNTIME":
                        while (items[i+1] != "CURKU") //Due to multiple cards, perform micro-loop
                        {
                            collection.Add("EXEC_RUNTIME" + countStep, Math.Round(Convert.ToDouble(Decimal.Parse(items[i + 1]), CultureInfo.InvariantCulture),2));
                            execRuntime += Convert.ToDouble(Decimal.Parse(items[i + 1]), CultureInfo.InvariantCulture);
                            countStep++;
                            i += 1;
                        }
                        collection.Add("EXEC_RUNTIME_AVG", Math.Round(execRuntime/ countStep,2)); //Calculate the average kernel run-time
                        collection.Add("EXEC_TIME_COUNT", countStep);

                        break;
                    case "CURKU":
                        collection.Add("CURKU", Convert.ToDouble(items[i + 1]));
                        i += 1;
                        break;
                    case "PROGRESS":
                        collection.Add("PROGRESS1", Convert.ToDouble(items[i + 1])); //First progress value
                        collection.Add("PROGRESS2", Convert.ToDouble(items[i + 2])); //Total progress value
                        collection.Add("PROGRESS_DIV", Math.Round(Convert.ToDouble(items[i + 1])/Convert.ToInt64(items[i + 2]),15)); //Total progress value
                        i += 2;
                        break;
                    case "RECHASH":
                        collection.Add("RECHASH1", Convert.ToDouble(items[i + 1])); //First RECHASH value
                        collection.Add("RECHASH2", Convert.ToDouble(items[i + 2])); //Second RECHASH value
                        i += 2;
                        break;
                    case "RECSALT":
                        collection.Add("RECSALT1", Convert.ToDouble(items[i + 1])); //First RECSALT value
                        collection.Add("RECSALT2", Convert.ToDouble(items[i + 2])); //Second RECSALT value
                        i += 2;
                        break;
                    case "REJECTED":
                        collection.Add("REJECTED", Convert.ToDouble(items[i + 1]));
                        collection.Add("PROGRESS_REJ", Math.Round((collection["PROGRESS1"]-collection["REJECTED"]) / collection["PROGRESS2"], 15)); //Total progress value
                        i += 1;
                        break;
                    case "UTIL":
                        while (items[i + 1] != "") //Due to multiple cards, perform micro-loop
                        {
                            collection.Add("UTIL" + countStep, Convert.ToDouble(items[i + 1]));
                            countStep++;
                            i += 2;
                        }
                        break;
                    case "TEMP":
                        while (items[i + 1] != "REJECTED") //Due to multiple cards, perform micro-loop
                        {
                            collection.Add("TEMP" + countStep, Convert.ToDouble(items[i + 1]));
                            countStep++;
                            i += 2;
                        }
                        break;

                }
                i += 1;
            }

            string[] Vars = new String[] { "STATUS", "SPEED_TOTAL", "EXEC_RUNTIME_AVG", "CURKU", "PROGRESS1","RECHASH1","RECSALT1" };
            foreach (string variable in Vars)
            {
                if (!collection.ContainsKey(variable))
                {
                    Console.WriteLine("Failed to parse {0} variable, something went wrong", variable);
                }
            }
        }


        private void parseStatus2(string statusLine, ref Dictionary<string, double> collection)
        {

            CultureInfo customCulture = (CultureInfo)System.Threading.Thread.CurrentThread.CurrentCulture.Clone();
            customCulture.NumberFormat.NumberDecimalSeparator = ".";
            System.Threading.Thread.CurrentThread.CurrentCulture = customCulture;

            Match match = Regex.Match(statusLine, ":[0-9]{1,}:[0-9.]{1,}(\n|\r|\r\n)", RegexOptions.IgnoreCase); //Match only the progress line using regex
            long counter = 0;
            double leftT = 0;
            double rightT = 0;

            while (match.Success)
            {

                string[] items = match.ToString().TrimEnd().Split(':');


                collection.Add("LEFT" + counter, Convert.ToDouble(Decimal.Parse(items[1],CultureInfo.InvariantCulture)));
                collection.Add("RIGHT" + counter, Convert.ToDouble(Decimal.Parse(items[2], CultureInfo.InvariantCulture)));
                leftT += Convert.ToDouble(Decimal.Parse(items[1], CultureInfo.InvariantCulture));
                rightT += Convert.ToDouble(Decimal.Parse(items[2], CultureInfo.InvariantCulture));
                counter++;
                match = match.NextMatch();
            }
            collection.Add("LEFT_TOTAL" ,leftT);
            collection.Add("RIGHT_TOTAL", rightT);

        }

        public Boolean runBenchmark(int benchMethod, int benchSecs, ref Dictionary<string, double> collection,Boolean legacy)
        {

            StringBuilder stdOutBuild = new StringBuilder();

            string suffixArgs = " --restore-disable --potfile-disable  --machine-readable --session=hashtopolis";
            string suffixExtra = "";

            if (benchMethod == 1)
            {
                suffixExtra = " --runtime=" + benchSecs; 
            }
            else if (benchMethod == 2)
            {
                suffixExtra = " --progress-only";
            }
            
            if (legacy) //--weak was removed post HC 3.6, don't issue this command
            {
                suffixArgs = suffixArgs + "--weak=0" + suffixExtra;
            }
            else
            {
                suffixArgs = suffixArgs + suffixExtra;
            }

            ProcessStartInfo pInfo = new ProcessStartInfo();
            pInfo.FileName = Path.Combine(hcDirectory, hcBinary);
            
            if (!File.Exists(pInfo.FileName))
            {
                Console.WriteLine("Could not locate " + pInfo.FileName);
                return false;
            }

            pInfo.WorkingDirectory = hcDirectory;
            pInfo.Arguments = hcArgs + suffixArgs;
            pInfo.UseShellExecute = false;
            pInfo.RedirectStandardError = true;
            pInfo.RedirectStandardOutput = true;
            

            if (debugFlag)
            {
                Console.WriteLine("Using {0} as working directory", filesDir);
                Console.WriteLine(pInfo.FileName + pInfo.Arguments);
            }
            

            Process hcProcBenchmark = new Process();
            hcProcBenchmark.StartInfo = pInfo;

            hcProcBenchmark.ErrorDataReceived += (sender, argu) => outputError(argu.Data);

            if (benchMethod == 1)
            {
                Console.WriteLine("Server requested the client benchmark this task for {0} seconds", benchSecs);

            }
            else
            {
                Console.WriteLine("Server has requested the client perform a speed benchmark");

            }
            try
            {
                hcProcBenchmark.Start();
                hcProcBenchmark.BeginErrorReadLine();
                
                while (!hcProcBenchmark.HasExited)
                {
                    while (!hcProcBenchmark.StandardOutput.EndOfStream)
                    {

                        string stdOut = hcProcBenchmark.StandardOutput.ReadLine().TrimEnd();
                        stdOutBuild.AppendLine(stdOut);
                        if (stdOut.Contains("STATUS\t") && benchMethod !=2)
                        {
            
                            {
                                parseStatus1(stdOut, ref collection);
                            }
                            
                            break;
                        }
                    }
                }
                hcProcBenchmark.StandardOutput.Close();

            }
            finally
            {
                hcProcBenchmark.Close();
            }

            if (stdOutBuild.ToString().Contains("Parsing Hashes: 0/")) //Can read from stderr for no hashes loaded, but this also works.
            {
                return false;
            }
            else
            {
                Console.WriteLine(stdOutBuild.ToString());
            }

            if (benchMethod == 2)
            {
                parseStatus2(stdOutBuild.ToString(),ref collection);
            }

            return true;
        }

        private static void parseKeyspace(string line, ref long keySpace)
        {
            line = line.TrimEnd();

            if (!long.TryParse(line, out keySpace))
            {
                Console.WriteLine("There was an error parsing the keyspace, setting keyspace to 0. Please review attack cmd");
                keySpace = 0; //Return 0 which will throw error
            }

        }

        public string getVersion2(ref string[] versionNum)
        {
            ProcessStartInfo pInfo = new ProcessStartInfo();
            pInfo.FileName = Path.Combine(hcDir, hcBin);
            pInfo.WorkingDirectory = filesDir;
            pInfo.Arguments = "--version";
            pInfo.UseShellExecute = false;
            pInfo.RedirectStandardError = true;
            pInfo.RedirectStandardOutput = true;
            Process hcGetVersion = new Process();

            hcGetVersion.StartInfo = pInfo;
            string versionString = "";

            try
            {
                hcGetVersion.Start();
                versionString = hcGetVersion.StandardOutput.ReadToEnd().TrimEnd();
                hcGetVersion.WaitForExit();

                Regex regex = new Regex("v(?<version>[^-]*)");

                Match match = regex.Match(versionString);

                if (match.Success)
                {
                    versionNum = match.Groups["version"].Value.Split('.');

                }
                else
                {
                    versionNum = versionString.Split('.');  //Hashcat changed the output after 3.6 to exclude the version string
                }
            }
            catch
            {
                Console.WriteLine("Something went wrong when trying to get HC version");
            }
            finally
            {
                if (hcGetVersion.ExitCode != 0)
                {
                    Console.WriteLine("Something went when trying to get HC version");
                }

                hcGetVersion.Close();
            }

            return versionString;
        }
        public string getVersion()
        {

            string stdOutSingle = "";
            ProcessStartInfo pInfo = new ProcessStartInfo();
            pInfo.FileName = Path.Combine(hcDir, hcBin);
            pInfo.WorkingDirectory = filesDir;
            pInfo.Arguments = "--version";
            pInfo.UseShellExecute = false;
            pInfo.RedirectStandardError = true;
            pInfo.RedirectStandardOutput = true;
            Process hcGetVersion = new Process();
            hcGetVersion.StartInfo = pInfo;
            hcGetVersion.ErrorDataReceived += (sender, argu) => outputError(argu.Data);

            try
            {

                hcGetVersion.Start();
                while (!hcGetVersion.HasExited)
                {
                    while (!hcGetVersion.StandardOutput.EndOfStream)
                    {

                        string stdOut = hcGetVersion.StandardOutput.ReadLine().TrimEnd();
                        stdOutSingle = stdOut; //We just want the last line
                    }
                }
                hcGetVersion.StandardOutput.Close();

            }
            catch
            {
                Console.WriteLine("Something went wrong when trying to get HC version");
            }
            finally
            {

                hcGetVersion.Close();
            }

            return stdOutSingle;


        }

        public Boolean runKeyspace(ref long keySpace)
        {

            Console.WriteLine("Server has requested the client measure the keyspace for this task");

            string stdOutSingle = "";
            string suffixArgs = " --session=hashtopolis --keyspace --quiet";
            ProcessStartInfo pInfo = new ProcessStartInfo();
            pInfo.FileName =  Path.Combine(hcDirectory, hcBinary);

            if (!File.Exists(pInfo.FileName))
            {
                Console.WriteLine("Could not locate " + pInfo.FileName);
                return false;
            }

            pInfo.WorkingDirectory = hcDirectory;


            pInfo.Arguments = hcArgs + suffixArgs;
            pInfo.UseShellExecute = false;
            pInfo.RedirectStandardError = true;
            pInfo.RedirectStandardOutput = true;
            if (debugFlag)
            {
                Console.WriteLine("Using {0} as working directory", pInfo.WorkingDirectory);
                Console.WriteLine(pInfo.FileName + " " + pInfo.Arguments);
            }

            Process hcProcKeyspace = new Process();
            hcProcKeyspace.StartInfo = pInfo;
            hcProcKeyspace.ErrorDataReceived += (sender, argu) => outputError(argu.Data);

            try
            {
                hcProcKeyspace.Start();
                hcProcKeyspace.BeginErrorReadLine();

                while (!hcProcKeyspace.HasExited)
                {
                    while (!hcProcKeyspace.StandardOutput.EndOfStream)
                    {
                        string stdOut = hcProcKeyspace.StandardOutput.ReadLine().TrimEnd();
                        stdOutSingle = stdOut; //We just want the last line
                    }
                }
                hcProcKeyspace.StandardOutput.Close();

            }
            catch
            {
                Console.WriteLine("Something went wrong with keyspace measuring");
            }
            finally
            {
                if (hcProcKeyspace.ExitCode != 0)
                {
                    Console.WriteLine("Something went wrong with keyspace measuring");
                }

                hcProcKeyspace.Close();
            }

            parseKeyspace(stdOutSingle,ref keySpace);

            return true;
        }

        public static void outputError(string stdError)
        {
            if (!string.IsNullOrEmpty(stdError))
            {
                Console.WriteLine(stdError.Trim());
            }

        }


        //There is very little discruption to the attack as a very quick lock/unlock is performed on the packet list to pop the job off the queue
        public void threadReadOutfile(ref List<Packets> uploadPackets, ref object objPacketlock)
        {
            System.Globalization.CultureInfo customCulture = (System.Globalization.CultureInfo)System.Threading.Thread.CurrentThread.CurrentCulture.Clone();
            customCulture.NumberFormat.NumberDecimalSeparator = ".";
            System.Threading.Thread.CurrentThread.CurrentCulture = customCulture;

        }

            public void stdOutTrigger(string stdOut)
        {

            if (!string.IsNullOrEmpty(stdOut))
            {

                if ((!stdOut.Contains("STATUS\t") && (!stdOut.Contains("EXEC_RUNTIME\t")) && (!stdOut.Contains("CURKU\t"))))
                {
                    if (stdOut.StartsWith("Hashfile"))
                    {
                        if (!stdOut.Contains("Line-length exception"))
                        {
                            lock (crackedLock)
                            {
                                hashlist.Add(stdOut);
                            }
                        }
                        else
                        {
                            lock (crackedLock)
                            {
                                hashlist.Add(stdOut);
                            }
                        }
                    }
                    else
                    {
                        lock (crackedLock)
                        {
                            hashlist.Add(stdOut);
                        }
                    }
                }

                else

                {
                    lock (statusLock)
                    {
                        Dictionary<string, double> dStats = new Dictionary<string, double>();

                        parseStatus1(stdOut, ref dStats);


                        lock (packetLock)
                        {
                            lock (crackedLock)
                            {
                                passedPackets.Add(new Packets { statusPackets = new Dictionary<string, double>(dStats), crackedPackets = new List<string>(hashlist) });
                                dStats.Clear();
                                hashlist.Clear();
                            }
                        }
                    }
                }

            }
        }



        public Boolean startAttack(long chunk, long taskID, long skip, long size, long interval, string taskPath)
        {

            string oPath = Path.Combine(taskPath, taskID + "_" + chunk + ".txt"); // Path to write th -o file
            if (File.Exists(oPath))
            {
                File.Delete(oPath); // We need to wipe the outfile if it exists since we want to start at pos 0
            }

            ProcessStartInfo pInfo = new ProcessStartInfo();

            pInfo.FileName = Path.Combine(hcDir, hcBin);

            if (!File.Exists(pInfo.FileName))
            {
                Console.WriteLine("Could not locate " + pInfo.FileName);
                return false;
            }

            pInfo.Arguments = hcArgs + " --potfile-disable --quiet --restore-disable --session=hashtopolis --status --machine-readable --status-timer=" + interval + " --outfile-check-timer=" + interval + " --remove --remove-timer=" + interval  + " -s " + skip + " -l " + size;
            pInfo.WorkingDirectory = hcDirectory;
            pInfo.UseShellExecute = false;
            pInfo.RedirectStandardError = true;
            pInfo.RedirectStandardOutput = true;

            if (debugFlag)
            {
                Console.WriteLine(pInfo.FileName + " " + pInfo.Arguments);
            }

            hcProc = new Process { };
            hcProc.StartInfo = pInfo;
            // create event handlers for normal and error output

            hcProc.OutputDataReceived += (sender, argu) => stdOutTrigger(argu.Data);
            hcProc.ErrorDataReceived += (sender, argu) => outputError(argu.Data);
            hcProc.EnableRaisingEvents = true;
            hcProc.Start();
            hcProc.BeginOutputReadLine();
            hcProc.BeginErrorReadLine();

            hcProc.WaitForExit();
            hcProc.CancelErrorRead();
            hcProc.CancelOutputRead();
            if (debugFlag)
            {
                Console.WriteLine("Attack finished");
            }
                

            hcProc.Dispose();

            return true;

        }
    }
}
