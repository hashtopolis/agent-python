using System;
using System.Diagnostics;
using System.Net;
using System.Threading;
using System.IO;

namespace hashtopussy
{
    class downloadClass
    {

        WebClient webClient;
        Stopwatch sw = new Stopwatch();

        public bool DownloadFile(string urlAddress, string location)
        {
            using (webClient = new WebClient())
            {
                webClient.DownloadProgressChanged += new DownloadProgressChangedEventHandler(ProgressChanged);

                // The variable that will be holding the url address (making sure it starts with http://)
                Uri URL = urlAddress.StartsWith("https://", StringComparison.OrdinalIgnoreCase) ? new Uri(urlAddress) : new Uri("https://" + urlAddress);

                Console.WriteLine(urlAddress);
                Console.WriteLine(location);
                // Start the stopwatch which we will be using to calculate the download speed
                sw.Start();

                try
                {
                    // Start downloading the file
                    webClient.DownloadFileAsync(URL, location);
                }
                catch (Exception ex)
                {
                    Console.WriteLine(ex.Message);
                    return false;
                }
                while (webClient.IsBusy) Thread.Sleep(500);
                
                if (File.Exists(location))
                    {
                    FileInfo f = new FileInfo(location);
                    long size = f.Length;
                    //Console.WriteLine(string.Format(" completed @ {0} kb/s", (size / 1024d / sw.Elapsed.TotalSeconds).ToString("0.00")));
                    Console.WriteLine();
                    return true;
                }
                else
                {
                    return false;
                }

            }
        }

        // The event that will fire whenever the progress of the WebClient is changed
        private void ProgressChanged(object sender, DownloadProgressChangedEventArgs e)
        {
            // Calculate download speed and output it to labelSpeed.
            //Console.WriteLine (string.Format("{0} kb/s", (e.BytesReceived / 1024d / sw.Elapsed.TotalSeconds).ToString("0.00")));

            // Update the progressbar percentage only when the value is not the same.
            //Console.WriteLine( e.ProgressPercentage);
            Console.Write("\r{0} {1}% @ {2} kb/s", "Downloading",e.ProgressPercentage, (e.BytesReceived / 1024d / sw.Elapsed.TotalSeconds).ToString("0.00"));
            // Update the label with how much data have been downloaded so far and the total size of the file we are currently downloading
            /*
            Console.WriteLine(string.Format("{0} MB's / {1} MB's",
                (e.BytesReceived / 1024d / 1024d).ToString("0.00"),
                (e.TotalBytesToReceive / 1024d / 1024d).ToString("0.00")));
            */
        }


    }
}
