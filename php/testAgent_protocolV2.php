<?php
/**
 * NOTE: This client is thought as a very simple test which is mainly used for testing purposes and not to be used
 * as a productive client with real cracking.
 */

$VERSION = "0.2.0";
$URL = "https://example.org/htp-test/src/api/server.php";
$OS = 0;

$TOKEN = null;
if (file_exists("token")) {
  $TOKEN = file_get_contents("token");
}
$RUNNING = true;
$INFORMATION_UPDATE = false;
$UPDATECHECK = false;
$LOGGEDIN = false;
$DOWNLOADCHECKDONE = false;
$BINARY = "";
$TASK = null;
$BENCH = false;
$KEYSPACE = false;
$CHUNK = null;
$lastPercent = 0;
while ($RUNNING) {
  $BINARY = "hashcat";
  if ($TOKEN == null) {
    register();
    continue;
  }
  else if (!$INFORMATION_UPDATE) {
    sendInformation();
    sleep(5);
    continue;
  }
  else if (!$UPDATECHECK) {
    checkForUpdate();
    continue;
  }
  else if (!$LOGGEDIN) {
    login();
    continue;
  }
  else if (!$DOWNLOADCHECKDONE) {
    checkDownload();
    continue;
  }
  else if ($TASK == null) {
    getTask();
  }
  else if ($TASK != null && $CHUNK == null) {
    if ($BENCH) {
      //do benchmark
      doBenchmark();
    }
    else if ($KEYSPACE) {
      //calculate keyspace
      doKeyspace();
    }
    else {
      getChunk();
    }
  }
  else if ($TASK != null && $CHUNK != null) {
    runTask();
    die();
  }
}

echo "Bye :)\n";


function runTask() {
  global $TASK, $TOKEN, $BINARY, $CHUNK;
  if (file_exists("hashlists/zaps")) {
    system("rm -r hashlists/zaps");
  }
  mkdir("hashlists/zaps");
  $founds = array();
  
  $command = "hashcat/$BINARY --skip=" . $CHUNK['skip'] . " --limit=" . ($CHUNK['skip'] + $CHUNK['length']) . " --outfile-check-dir hashlists/zaps --potfile-disable --machine-readable --status --status-timer=" . $TASK['statustimer'] . " " . $TASK['cmdpars'] . " " . str_replace("#HL#", "hashlists/hl" . $TASK['hashlist'], $TASK['attackcmd']);
  echo $command . "\n";
  $running = popen($command, "r");
  echo "Command started...\n";
  $skipping = 0;
  while (!feof($running)) {
    $line = trim(fgets($running));
    if (strpos($line, "STATUS") !== false) {
      $split = explode("\t", $line);
      if ($skipping > 0) {
        echo "skipping $skipping...\n";
        $skipping--;
        continue;
      }
      echo "STATUS\n";
      $query = array("action" => "solve", "token" => $TOKEN, "chunk" => $CHUNK['chunk'], "keyspaceProgress" => $split[8], "progress" => $split[10], "total" => $split[11], "speed" => $split[3], "state" => $split[1], "cracks" => $founds);
      $start = time();
      $ans = doRequest($query);
      $required = time() - $start;
      if ($required > $TASK['statustimer']) {
        $skipping = floor($required / ($TASK['statustimer'] * 2));
      }
      if ($ans == null) {
        echo "Solve command failed!\n";
      }
      else {
        echo "Cracks sent!\n";
        $founds = array();
      }
    }
    else if (strpos($line, "\r") !== false) {
      $line = explode("\r", $line);
      $founds[] = $line[sizeof($line) - 1];
    }
  }
  /*$query = array("action" => "solve", "token" => $TOKEN, "chunk" => $CHUNK['chunk'], "keyspaceProgress" => $split[8], "progress" => $split[10], "total" => $split[11], "speed" => $split[3], "state" => $split[1], "cracks" => $founds);
  doRequest($query);*/
  pclose($running);
  echo "Command finished!\n";
}

function doKeyspace() {
  global $TASK, $TOKEN, $KEYSPACE, $BINARY;
  
  $command = "hashcat/$BINARY --keyspace " . $TASK['cmdpars'] . " " . str_replace("#HL#", "", $TASK['attackcmd']);
  $output = array();
  echo $command . "\n";
  exec($command, $output);
  if (sizeof($output) != 1) {
    die("Something went wrong when calculating the keyspace!\n");
  }
  $space = intval($output[0]);
  $query = array("action" => "keyspace", "token" => $TOKEN, "taskId" => $TASK['task'], "keyspace" => $space);
  $ans = doRequest($query);
  if ($ans == null) {
    echo "Failed to send keyspace!\n";
    sleep(5);
    return;
  }
  else {
    echo "Keyspace sent!\n";
  }
  $KEYSPACE = false;
}

function doBenchmark() {
  global $TASK, $TOKEN, $BENCH, $BINARY;
  
  $command = "hashcat/$BINARY --machine-readable " . $TASK['cmdpars'] . " " . str_replace("#HL#", "hashlists/hl" . $TASK['hashlist'], $TASK['attackcmd']);
  $descriptorspec = array(
    0 => array("pipe", "r"),  // STDIN ist eine Pipe, von der das Child liest
    1 => array("pipe", "w"),  // STDOUT ist eine Pipe, in die das Child schreibt
    2 => array("file", "/tmp/error-output.txt", "a") // STDERR ist eine Datei, in die geschrieben wird
  );
  $pipes = array();
  $process = proc_open($command, $descriptorspec, $pipes);
  
  if (is_resource($process)) {
    sleep(30);
    fwrite($pipes[0], "s");
    fwrite($pipes[0], "q");
    fclose($pipes[0]);
    
    $output = stream_get_contents($pipes[1]);
    $output = explode("\n", $output);
    $lastStatus = null;
    foreach ($output as $line) {
      if (strpos($line, "STATUS") === 0) {
        $lastStatus = $line;
      }
    }
    if ($lastStatus == null) {
      die("Error on determining last status on benchmarking!");
    }
    $lastStatus = explode("\t", $lastStatus);
    $bench = $lastStatus[10] / $lastStatus[11];
    
    fclose($pipes[1]);
    proc_close($process);
    
    echo "Hashcat benchmarking done!\n";
  }
  else {
    die("Hashcat benchmarking failed!\n");
  }
  
  $query = array("action" => "bench", "token" => $TOKEN, "taskId" => $TASK['task'], "speed" => $bench);
  $ans = doRequest($query);
  if ($ans == null) {
    echo "Failed to send benchmark result!\n";
    sleep(5);
    return;
  }
  echo "Benchmark sent!\n";
  $BENCH = false;
}

function getChunk() {
  global $TOKEN, $CHUNK, $BENCH, $KEYSPACE, $TASK;
  
  $query = array("action" => "chunk", "token" => $TOKEN, "taskId" => $TASK['task']);
  $ans = doRequest($query);
  if ($ans == null) {
    echo "Failed to get chunk!\n";
    sleep(10);
  }
  else if ($ans['chunk'] == 'fully_dispatched') {
    echo "Task is already fully dispatched, get another one...\n";
    $TASK = null;
  }
  else if ($ans['chunk'] == 'keyspace_required') {
    echo "Keyspace calculation is required for this task!\n";
    $KEYSPACE = true;
  }
  else if ($ans['chunk'] == "benchmark") {
    echo "Benchmarking of agent required!\n";
    $BENCH = true;
  }
  else {
    echo "Successfully got chunk!\n";
    $CHUNK = $ans;
  }
}

function getTask() {
  global $TOKEN, $TASK;
  
  $query = array("action" => "task", "token" => $TOKEN);
  $ans = doRequest($query);
  if ($ans == null) {
    echo "Failed to get task!\n";
    sleep(10);
  }
  else if ($ans['task'] == 'NONE') {
    echo "Currently no task available...\n";
    sleep(10);
  }
  else {
    $TASK = $ans;
    handleDependencies();
  }
}

function downloadHashlist($id) {
  global $TOKEN;
  
  if (!file_exists("hashlists")) {
    mkdir("hashlists");
  }
  $query = array("action" => "hashes", "token" => $TOKEN, "hashlist" => $id);
  
  //download hashlist with given id
  doDownloadRequest($query, "hashlists/hl$id");
  //check if the hashlist was downloaded or if there an error occured
  $check = fopen("hashlists/hl$id", "rb");
  $line = fgets($check);
  fclose($check);
  if (strlen($line) == 0 || $line[0] == '{') {
    $info = "";
    if (file_exists("hashlists/hl$id") && filesize("hashlists/hl$id") < 100000) {
      $info = file_get_contents("hashlists/hl$id");
    }
    echo "There was an error when downloading the hashlist! " . $info . "\n";
    unlink("hashlists/hl$id");
    die();
  }
  echo "Hashlist $id downloaded!\n";
}

function handleDependencies() {
  global $TOKEN, $TASK;
  
  $hashlist = $TASK['hashlist'];
  $files = $TASK['files'];
  if (!file_exists("hashlists/$hashlist")) {
    downloadHashlist($hashlist);
  }
  foreach ($files as $file) {
    if (!file_exists("files")) {
      mkdir("files");
    }
    $query = array("action" => "file", "token" => $TOKEN, "file" => $file, "task" => $TASK['task']);
    $ans = doRequest($query);
    if ($ans == null) {
      echo "Failed to get required file $file!\n";
      die();
    }
    
    if (file_exists("files/" . $ans['filename'])) {
      continue;
    }
    $url = $ans['url'];
    $file = $ans['filename'];
    echo "Downloading file $file...\n";
    doDownload($url, "files/" . $ans['filename']);
    echo "Download finished!\n";
    $extension = $ans['extension'];
    if ($extension == '7z') {
      echo "Extract $file...\n";
      extractFile($file);
    }
  }
}

function extractFile($file) {
  global $OS;
  
  if ($OS == 1) {
    //TODO:
  }
  else {
    system("cd files && 7z x $file");
  }
}

function checkDownload() {
  global $TOKEN, $DOWNLOADCHECKDONE, $OS, $BINARY;
  
  //check 7z
  if (!file_exists("7zr") && $OS == 1) {
    $query = array("action" => "download", "type" => "7zr", "token" => $TOKEN);
    $ans = doRequest($query, true);
    if ($ans == null) {
      die("7zr download failed!\n");
    }
    echo "Downloaded 7z extractor.\n";
    file_put_contents("7zr", $ans);
    chmod("7zr", 0777);
  }
  $hcinfo = null;
  if (!file_exists("hashcat")) {
    $query = array("action" => "download", "type" => "hashcat", "token" => $TOKEN, "force" => "1");
    $ans = doRequest($query);
    if ($ans == null) {
      echo "Cannot continue..\n";
      die();
    }
    $url = $ans['url'];
    $hcinfo = $ans;
    doDownload($url, "hashcat.7z");
    $BINARY = $ans['executable'];
    echo "Downloaded new hashcat!\n";
  }
  else {
    $query = array("action" => "download", "type" => "hashcat", "token" => $TOKEN, "force" => "0");
    $ans = doRequest($query);
    if ($ans == null) {
      echo "Failed to check for hashcat update!\n";
    }
    else {
      if ($ans['version'] == 'NEW') {
        //new hashcat available
        $url = $ans['url'];
        $hcinfo = $ans;
        doDownload($url, "hashcat.7z");
        echo "Downloaded new hashcat!\n";
      }
      $BINARY = $ans['executable'];
    }
  }
  if (file_exists("hashcat.7z") && $hcinfo != null) {
    if (file_exists("hashcat")) {
      deleteDir("hashcat");
    }
    if ($OS == 1) {
      system("7zr hashcat.7z");
    }
    else {
      system("7z x hashcat.7z");
    }
    mkdir("hashcat");
    foreach ($hcinfo['files'] as $file) {
      rename($hcinfo['rootdir'] . "/" . $file, "hashcat/" . $file);
    }
    deleteDir($hcinfo['rootdir']);
    unlink("hashcat.7z");
    echo "Extracted new hashcat!\n";
  }
  $DOWNLOADCHECKDONE = true;
}

function deleteDir($dirPath) {
  if (!is_dir($dirPath)) {
    throw new InvalidArgumentException("$dirPath must be a directory");
  }
  if (substr($dirPath, strlen($dirPath) - 1, 1) != '/') {
    $dirPath .= '/';
  }
  $files = glob($dirPath . '*', GLOB_MARK);
  foreach ($files as $file) {
    if (is_dir($file)) {
      deleteDir($file);
    }
    else {
      unlink($file);
    }
  }
  rmdir($dirPath);
}

function login() {
  global $LOGGEDIN, $TOKEN;
  
  $query = array("action" => "login", "token" => $TOKEN);
  $ans = doRequest($query);
  if ($ans != null) {
    echo "Logged in successfully!\n";
    $LOGGEDIN = true;
  }
}

function checkForUpdate() {
  global $UPDATECHECK;
  
  $UPDATECHECK = true;
  //TODO: implement update
}

function register() {
  global $TOKEN;
  
  $query = array("action" => "register");
  $query['name'] = explode(" ", php_uname())[1];
  echo "Please insert the voucher:\n";
  $query['voucher'] = readline();
  
  $ans = doRequest($query);
  if ($ans != null) {
    $TOKEN = $ans['token'];
    file_put_contents("token", $TOKEN);
    echo "Registration successfull!\n";
  }
}

function sendInformation() {
  global $TOKEN, $INFORMATION_UPDATE;
  
  $query = array("action" => "updateInformation");
  $query['uid'] = posix_getuid();
  $query['os'] = PHP_OS;
  $query['devices'] = array("mockGPU1", "mockGPU2");
  $query['token'] = $TOKEN;
  $ans = doRequest($query);
  if ($ans != null) {
    echo "Updated client information!\n";
    $INFORMATION_UPDATE = true;
  }
}

function doDownloadRequest($query, $file) {
  global $URL;
  
  //send query
  $ch = curl_init();
  
  curl_setopt($ch, CURLOPT_FILE, fopen($file, "wb"));
  curl_setopt($ch, CURLOPT_TIMEOUT, 28800); // set this to 8 hours so we dont timeout on big files
  curl_setopt($ch, CURLOPT_URL, $URL);
  curl_setopt($ch, CURLOPT_POST, 1);
  curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query(array("query" => json_encode($query))));
  
  
  curl_exec($ch);
}

function doDownload($url, $save) {
  global $lastPercent;
  
  set_time_limit(0); // unlimited max execution time
  $lastPercent = 0;
  $options = array(
    CURLOPT_FILE => fopen($save, "wb"),
    CURLOPT_TIMEOUT => 28800, // set this to 8 hours so we dont timeout on big files
    CURLOPT_URL => $url,
    CURLOPT_PROGRESSFUNCTION => 'progress'
  );
  
  $ch = curl_init();
  curl_setopt_array($ch, $options);
  curl_exec($ch);
  curl_close($ch);
}

function progress($resource, $download_size, $downloaded, $upload_size, $uploaded) {
  global $lastPercent;
  
  if ($download_size > 0) {
    $percent = round($downloaded / $download_size * 100);
    if ($percent > $lastPercent) {
      echo "$percent%     \r";
      $lastPercent = $percent;
    }
  }
  ob_flush();
  flush();
}

function doRequest($query, $binaryExptected = false) {
  global $URL;
  
  //send query
  $ch = curl_init();
  
  curl_setopt($ch, CURLOPT_URL, $URL);
  curl_setopt($ch, CURLOPT_POST, 1);
  curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($query));


// receive server response ...
  curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
  
  $server_output = curl_exec($ch);
  
  curl_close($ch);
  if ($binaryExptected) {
    $answer = json_decode($server_output, true);
    if ($answer['response'] == 'ERROR') {
      echo "FAILED: " . $answer['message'] . "\n";
      return null;
    }
    else if (strlen($server_output) == 0) {
      return null;
    }
    else {
      return $server_output;
    }
  }
  
  $answer = json_decode($server_output, true);
  print_r($answer);
  if ($answer['response'] == 'ERROR') {
    echo "FAILED: " . $answer['message'] . "\n";
  }
  else if ($answer['response'] != 'SUCCESS') {
    echo "Unexpected Error: $server_output\n";
  }
  else {
    return $answer;
  }
  return null;
}


die();

$select = @$argv[1];

$query = array();

switch ($select) {
  case 'register':
    $query['action'] = "register";
    $query['voucher'] = $argv[2];
    $query['uid'] = "jhajheowfhke";
    $query['name'] = "new client";
    $query['os'] = "Windows";
    $query['gpus'] = array("ATI HD 7970", "ATI HD 7970");
    break;
  default:
    die("ERROR");
}

//send query
$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, "http://localhost/hashtopussy/src/server.php");
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query(array("query" => json_encode($query))));


// receive server response ...
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

$server_output = curl_exec($ch);

curl_close($ch);

echo $server_output . "\n";


/*
 * "action":"register",
  "voucher":"89GD78tf",
  "uid":"230-34-345-345",
  "name":"client name",
  "os":0,
  "gpus":[
    "ATI HD7970",
    "ATI HD7970"
  ]
 */