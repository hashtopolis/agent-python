<?php
/**
 * Created by IntelliJ IDEA.
 * User: sein
 * Date: 10.11.16
 * Time: 13:15
 */

//TODO: implement auto update feature

$VERSION = "0.1.0";
$URL = "http://localhost/hashtopussy/src/api/server.php";
$OS = 0;

$TOKEN = null;
if (file_exists("token")) {
  $TOKEN = file_get_contents("token");
}
$RUNNING = true;
$UPDATECHECK = false;
$LOGGEDIN = false;
$DOWNLOADCHECKDONE = false;
$BINARY = "";
$TASK = null;
$BENCH = false;
$KEYSPACE = false;
$CHUNK = null;
while ($RUNNING) {
  if ($TOKEN == null) {
    register();
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
  else if($TASK == null){
    getTask();
  }
  else if($TASK != null && $CHUNK == null){
    if($BENCH){
      //do benchmark
      doBenchmark();
    }
    else if($KEYSPACE){
      //calculate keyspace
      doKeyspace();
    }
    else{
      getChunk();
    }
  }
  else if($TASK != null && $CHUNK != null){
    //do task
  }
}

echo "Bye :)\n";




function doKeyspace(){
  global $TASK, $TOKEN, $KEYSPACE, $BINARY;
  
  $command = "hashcat/$BINARY --keyspace ".$TASK['cmdpars']." ".str_replace("#HL#", "hashlists/hl".$TASK['hashlist'], $TASK['attackcmd']);
  $output = array();
  exec($command, $output);
  if(sizeof($output) != 1){
    die("Something went wrong when calculating the keyspace!\n");
  }
  $space = intval($output[0]);
  $query = array("action" => "keyspace", "token" => $TOKEN, "taskId" => $TASK['task'], "keyspace" => $space);
  $ans = doRequest($query);
  if($ans == null){
    echo "Failed to send keyspace!\n";
  }
  else{
    echo "Keyspace sent!\n";
  }
  $KEYSPACE = false;
}

function doBenchmark(){
  global $TASK, $TOKEN, $BENCH, $BINARY;
  
  //TODO: do benchmark
}

function getChunk(){
  global $TOKEN, $CHUNK, $BENCH, $KEYSPACE, $TASK;
  
  $query = array("action" => "chunk", "token" => $TOKEN, "taskId" => $TASK['task']);
  $ans = doRequest($query);
  if($ans == null){
    echo "Failed to get chunk!\n";
    sleep(10);
  }
  else if($ans['chunk'] == 'fully_dispatched'){
    echo "Task is already fully dispatched, get another one...\n";
    $TASK = null;
  }
  else if($ans['chunk'] == 'keyspace_required'){
    echo "Keyspace calculation is required for this task!\n";
    $KEYSPACE = true;
  }
  else if($ans['chunk'] == "benchmark"){
    echo "Benchmarking of agent required!\n";
    $BENCH = true;
  }
  else{
    $CHUNK = $ans;
  }
}

function getTask(){
  global $TOKEN, $TASK;
  
  $query = array("action" => "task", "token" => $TOKEN);
  $ans = doRequest($query);
  if($ans == null){
    echo "Failed to get task!\n";
    sleep(10);
  }
  else if($ans['task'] == 'NONE'){
    echo "Currently no task available...\n";
    sleep(10);
  }
  else{
    $TASK = $ans;
    handleDependencies();
  }
}

function downloadHashlist($id){
  global $TOKEN;
  
  if(!file_exists("hashlists")){
    mkdir("hashlists");
  }
  $query = array("action" => "hashes", "token" => $TOKEN, "hashlist" => $id);
  
  //download hashlist with given id
  doDownloadRequest($query, "hashlists/hl$id");
  //check if the hashlist was downloaded or if there an error occured
  $check = fopen("hashlists/hl$id", "rb");
  $line = fgets($check);
  fclose($check);
  if(strlen($line) == 0 || $line[0] == '{'){
    $info = "";
    if(file_exists("hashlists/hl$id") && filesize("hashlists/hl$id") < 100000){
      $info = file_get_contents("hashlists/hl$id");
    }
    echo "There was an error when downloading the hashlist! ".$info."\n";
    unlink("hashlists/hl$id");
    die();
  }
  echo "Hashlist $id downloaded!\n";
}

function handleDependencies(){
  global $TOKEN, $TASK;
  
  $hashlist = $TASK['hashlist'];
  $files = $TASK['files'];
  downloadHashlist($hashlist);
  foreach($files[0] as $file){
    if(file_exists("files/$file")){
      continue;
    }
    $query = array("action" => "file", "token" => $TOKEN, "file" => $file, "task" => $TASK['task']);
    $ans = doRequest($query);
    if($ans == null){
      echo "Failed to get required file $file!\n";
      die();
    }
    $url = $ans['url'];
    doDownload($url, "files/$file");
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
  $query['uid'] = posix_getuid();
  $query['os'] = PHP_OS;
  $query['name'] = explode(" ", php_uname())[1];
  $query['gpus'] = array("mockGPU");
  echo "Please insert the voucher:\n";
  $query['voucher'] = readline();
  
  $ans = doRequest($query);
  if ($ans != null) {
    $TOKEN = $ans['token'];
    file_put_contents("token", $TOKEN);
    echo "Registration successfull!\n";
  }
}

function doDownloadRequest($query, $file){
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
  set_time_limit(0); // unlimited max execution time
  $options = array(
    CURLOPT_FILE => fopen($save, "wb"),
    CURLOPT_TIMEOUT => 28800, // set this to 8 hours so we dont timeout on big files
    CURLOPT_URL => $url,
  );
  
  $ch = curl_init();
  curl_setopt_array($ch, $options);
  curl_exec($ch);
  curl_close($ch);
}

function doRequest($query, $binaryExptected = false) {
  global $URL;
  
  //send query
  $ch = curl_init();
  
  curl_setopt($ch, CURLOPT_URL, $URL);
  curl_setopt($ch, CURLOPT_POST, 1);
  curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query(array("query" => json_encode($query))));


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