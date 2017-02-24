using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Diagnostics;
using System.Collections.Specialized;
using System.Text.RegularExpressions;
using System.Globalization;
using System.Threading;

namespace hashtopussy
{
    class hashcatClass
    {
        public List<string> hashlist = new List<string> { }; //New collection to store cracks
        public Process hcProc;

        private string workingDir = "";
        private string filesDir = "";
        private string hcDir = "hashcat";
        private string hcBin = "hashcat64.exe";
        private string separator = "";

        private string hcArgs = "";
 
        private object packetLock;
        private object crackedLock;
        private object statusLock;


        List<Packets> passedPackets;


        public void setPassthrough(ref List<Packets> refPacketlist, ref object objpacketLock, string passSeparator)
        {
            passedPackets = refPacketlist;
            separator = passSeparator;
            packetLock = objpacketLock;

            crackedLock = new object();
            statusLock = new object();


        }
         
        public void setArgs(string args)
        {
            
            hcArgs = args;
        }

        public void setDirs(string fpath, int osID)
        {
            hcDir = Path.Combine(fpath, "hashcat");
            workingDir = Path.Combine(fpath, "tasks").TrimEnd();
            filesDir = Path.Combine(fpath, "files"," ").TrimEnd();

            if (osID == 0)
            {
                hcBin = "hashcat64.bin";
            }
            else if(osID == 2)
            {
                hcBin = "hashcat";
            }
            else
            {
                hcBin = "hashcat64.exe";
            }
        }

        public void runUpdate()
        {
            if (!Directory.Exists(hcDir))
            {
                //forceUpdate = true;
            }
        }



        public static void parseStatus1(string line,ref  Dictionary<string, double> collection)
        {


            Console.WriteLine(line);

            string[] items = line.Split('\t');
            double speedData = 0;
            double countStep = 0;
            double execRuntime = 0;

            int max = items.Count();
            int i = 0;


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
                            collection.Add(("SPEED" + countStep.ToString()), Convert.ToDouble(items[i + 1]));
                            speedData += Convert.ToDouble(items[i + 1]);
                            countStep++;
                            i += 2;
                        }
                        collection.Add("SPEED_TOTAL", speedData);
                        collection.Add("SPEED_COUNT", countStep);
                        break;
                    case "EXEC_RUNTIME":
                        while (items[i+1] != "CURKU") //Due to multiple cards, perform micro-loop
                        {
                            collection.Add(("EXEC_RUNTIME" + countStep.ToString()), Math.Round(Convert.ToDouble(Decimal.Parse(items[i + 1]), CultureInfo.InvariantCulture),2));
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
                    default:
                        i += 1;
                        break;
                    

                }
                i += 1;
            }
        }


        public static void parseStatus2(string statusLine, ref Dictionary<string, double> collection)
        {

            Match match = Regex.Match(statusLine, ":[0-9]{1,}:[0-9.]{1,}(\n|\r|\r\n)", RegexOptions.IgnoreCase); //Match only the progress line using regex
            long counter = 0;
            double leftT = 0;
            double rightT = 0;

            while (match.Success)
            {

                string[] items = match.ToString().TrimEnd().Split(':');


                collection.Add("LEFT" + counter.ToString(), Convert.ToDouble(Decimal.Parse(items[1],CultureInfo.InvariantCulture)));
                collection.Add("RIGHT" + counter.ToString(), Convert.ToDouble(Decimal.Parse(items[2], CultureInfo.InvariantCulture)));
                leftT += Convert.ToDouble(Decimal.Parse(items[1], CultureInfo.InvariantCulture));
                rightT += Convert.ToDouble(Decimal.Parse(items[2], CultureInfo.InvariantCulture));
                counter++;
                match = match.NextMatch();
            }
            collection.Add("LEFT_TOTAL" ,leftT);
            collection.Add("RIGHT_TOTAL", rightT);

        }

        public Boolean runBenchmark(int benchMethod, int benchSecs, ref Dictionary<string, double> collection)
        {

            StringBuilder stdOutBuild = new StringBuilder();


            string suffixExtra = "";
            if (benchMethod == 2)
            {
                suffixExtra = " --progress-only";
            }
            string suffixArgs = " --runtime=" + benchSecs + " --restore-disable --potfile-disable  --machine-readable --session=hashtopussy --weak=0" + suffixExtra;

            ProcessStartInfo pInfo = new ProcessStartInfo();
            pInfo.FileName = Path.Combine(hcDir, hcBin);
            Console.WriteLine("Using {0} as working directory", filesDir);
            pInfo.WorkingDirectory = filesDir;
            pInfo.Arguments = hcArgs + suffixArgs;
            pInfo.UseShellExecute = false;
            pInfo.RedirectStandardError = true;
            pInfo.RedirectStandardOutput = true;

            Console.WriteLine(pInfo.FileName + pInfo.Arguments);

            Process hcProcBenchmark = new Process();
            hcProcBenchmark.StartInfo = pInfo;

            hcProcBenchmark.ErrorDataReceived += (sender, argu) => outputError(argu.Data);

            if (benchMethod == 1)
            {
                Console.WriteLine("Server requsted the client benchark this task for {0} seconds", benchSecs);

            }
            else
            {
                Console.WriteLine("Server has requested the client to perform a speed benchmark");

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

            if (benchMethod == 2)
            {
                parseStatus2(stdOutBuild.ToString(),ref collection);
            }

            return true;
        }

        private static void parseKeyspace(string line, ref long keySpace)
        {
            line = line.TrimEnd();
            keySpace = Convert.ToInt64(line);
        }

        public Boolean runKeyspace(ref long keySpace)
        {

            Console.WriteLine("Server has requested the client to measure the keyspace for this task");

            StringBuilder stdOutBuild = new StringBuilder();
            string stdOutSingle = "";
            string suffixArgs = " --session=hashtopussy --keyspace --quiet";
            ProcessStartInfo pInfo = new ProcessStartInfo();
            pInfo.FileName = Path.Combine(hcDir , hcBin);
            pInfo.WorkingDirectory = filesDir;
            Console.WriteLine("Using {0} as working directory", filesDir);
            pInfo.Arguments = hcArgs + suffixArgs;
            pInfo.UseShellExecute = false;
            pInfo.RedirectStandardError = true;
            pInfo.RedirectStandardOutput = true;
            Console.WriteLine(pInfo.FileName + " " + pInfo.Arguments);
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

        public void stdOutTrigger(string stdOut)
        {

            if (!string.IsNullOrEmpty(stdOut))
            {
                
                if (stdOut.Contains(separator)) //Is a hit
                {
                    lock (crackedLock)
                    {
                        hashlist.Add(stdOut);
                    }
                    
                }
                else //Is a status output
                {

                    if (!stdOut.Contains("STATUS"))
                    {
                        return;
                    }

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
                    //Check if upload running, check if chunk has finished
            }
        }



        public Boolean startAttack(long chunk, long skip, long size, string separator, long interval, string taskPath)
        {


            ProcessStartInfo pinfo = new ProcessStartInfo();

            pinfo.FileName = Path.Combine(hcDir , hcBin);
            pinfo.Arguments = hcArgs + " --potfile-disable --quiet --restore-disable --session=hashtopussy --status --machine-readable --status-timer=" + interval + " --outfile-check-timer=" + interval + " --remove --remove-timer=" + interval + " --separator=" + separator + " -s " + skip + " -l " + size;
            pinfo.WorkingDirectory = filesDir;
            pinfo.UseShellExecute = false;
            pinfo.RedirectStandardError = true;
            pinfo.RedirectStandardOutput = true;

            Console.WriteLine(pinfo.FileName +" "+ pinfo.Arguments);

            hcProc = new Process { };
            hcProc.StartInfo = pinfo;
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
            Console.WriteLine("Attack finished");

            hcProc.Dispose();

            return true;

        }
    }
}
