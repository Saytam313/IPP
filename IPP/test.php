<?php
function test_finder($dir){
	#funkce prochazi zadanym adresarem a vyhledava testy
	#pokud je zadan argument --recursive je funkce rekurzivni
	#a pri nalezeni adresare se provede na nalezeny adresar
	global $parser;
	global $interpret;
	global $recursive;
	global $parseonly;
	global $intonly;
	global $failnute_testy;
	global $succes_testy;
	global $pocet_testu;
	global $failed_test;
	global $succes_test;
	$testdir = array_diff(scandir($dir), array('.', '..'));
	$testdir = array_values($testdir);
	
	for($i=0;$i<sizeof($testdir);$i++){
		if($recursive==True){
			#pri nalezeni adresare provede rekurzivni volani funkce test_finder
			if(is_dir("$dir/$testdir[$i]")){
				test_finder("$dir/$testdir[$i]");
			}
		}
		if(substr($testdir[$i], -3)=='src'){
			$pocet_testu++;
			$testfilename=substr($dir."/".$testdir[$i],0, -4);
			$testname=substr($testdir[$i],0, -4);
			#po nalezeni souboru s koncovkou .src najde a pripadne vygeneruje soubory s koncovkami .rc .in .out
			if(!in_array($testname.".rc", $testdir)){
				$rcfile = fopen($testfilename.".rc", "w");
				fwrite($rcfile,"0");
				fclose($rcfile);
			}
			if(!in_array($testname.".in", $testdir)){
				touch($testfilename.".in");
			}
			if(!in_array($testname.".out", $testdir)){
				touch($testfilename.".out");
			}
			#provadeni testu
			if($parseonly){
				exec("php7.3 '$parser' < '$testfilename.src'",$parser_res,$exit_res);
				$parser_res=implode(PHP_EOL,$parser_res);
				$rcfile = fopen($testfilename.".rc", "r");
				if(trim($exit_res)==trim(fread($rcfile,filesize($testfilename.".rc")))){
					if(trim($exit_res)==0){	
						#generace docasneho souboru
						$tmpfname=tempnam(".","tst");
						$tmpfile=fopen("$tmpfname", "w");
						#zapsani vysledku parseru do docasneho souboru
						fwrite($tmpfile, $parser_res);
						#porovnani XML nastrojem jexamxml
						$diff_res=shell_exec("java -jar /pub/courses/ipp/jexamxml/jexamxml.jar $tmpfname ".$testfilename.".out "."delta.xml /pub/courses/ipp/jexamxml/options");
						fclose($tmpfile);

						if(substr($diff_res,-24)=='Two files are identical\n'){
							array_push($failnute_testy,$testfilename);
							$failed_test++;
						}else{
							array_push($succes_testy,$testfilename);
							$succes_test++;
						}
						#smazani docasneho souboru
						unlink($tmpfname);
					}
				}else{
					array_push($failnute_testy,$testfilename);
					$failed_test++;
				}
				fclose($rcfile);
			}elseif($intonly){
				exec("python3 '$interpret' --source='$testfilename.src' --input='$testfilename.in'",$int_res, $exit_res);
				$int_res=implode(PHP_EOL,$int_res);

				$rcfile = fopen($testfilename.".rc", "r");
				if(trim($exit_res)==trim(fread($rcfile,filesize($testfilename.".rc")))){
					if(trim($exit_res)==0){	
						$tmpfname=tempnam(".","tst");
						$tmpfile=fopen("$tmpfname", "w");
						fwrite($tmpfile, $int_res);
						$diff_res=shell_exec("diff '$testfilename.out' $tmpfname");
						fclose($tmpfile);
						if($diff_res){
							array_push($failnute_testy,$testfilename);
							$failed_test++;
						}else{
							array_push($succes_testy,$testfilename);
							$succes_test++;
						}
						unlink($tmpfname);
					}else{
						array_push($succes_testy,$testfilename);
						$succes_test++;
					}
				}else{
					array_push($failnute_testy,$testfilename);
					$failed_test++;
				}
				fclose($rcfile);

			}else{
				exec("php7.3 '$parser' < '$testfilename.src'",$parser_res,$exit_res);
				$parser_res=implode(PHP_EOL,$parser_res);
				$rcfile = fopen($testfilename.".rc", "r");
				if(trim($exit_res)==0){
					$tmpfname=tempnam(".","tst");
					$tmpfile=fopen("$tmpfname", "w");
					fwrite($tmpfile, $parser_res);
					exec("python3 '$interpret' --input='$testfilename.in'"." --source=$tmpfname",$int_res, $exit_res);
					$int_res=implode(PHP_EOL,$int_res);					
					if(trim($exit_res)==trim(fread($rcfile,filesize($testfilename.".rc")))){
						if(trim($exit_res)==0){
							fclose($tmpfile);
							#vymazani obsahu docasneho souboru pro zapis vysledku interpretu
							$tmpfile=fopen("$tmpfname", "w");	
							fwrite($tmpfile, $int_res);

							$diff_res=shell_exec("diff ".$testfilename.".out $tmpfname");
							fclose($tmpfile);
							if($diff_res){
								array_push($failnute_testy,$testfilename);
								$failed_test++;
							}else{
								array_push($succes_testy,$testfilename);
								$succes_test++;
							}
						}else{
							array_push($succes_testy,$testfilename);
							$succes_test++;
						}
					}else{
						array_push($failnute_testy,$testfilename);
						$failed_test++;
					}
					unlink($tmpfname);
				}else{
					if(trim($exit_res)==trim(fread($rcfile,filesize($testfilename.".rc")))){
						array_push($succes_testy,$testfilename);
						$succes_test++;
					}else{
						array_push($failnute_testy,$testfilename);
						$failed_test++;
					}
				}
			}
		}
	

	}
	
}
$dirname=getcwd();
$parser="parse.php";
$interpret="interpret.py";
$recursive=False;
$parseonly=False;
$intonly=False;
#vyhledani pouzitych argumentu
for($i=1;$i<sizeof($argv);$i++){
	if($argv[$i]=="--help"){		
		echo("Skript slouzi pro automaticke testovani skriptu parse.php a interpret.py a na standartni vystup vypise vysledky do HTML5\n"
		."\nSpusteni:\n"
		."	php7.3 test.php [argumenty]\n"			
		."Argumenty:\n"
		."	--help - vypise tuto napovedu\n"
		."	--directory=(path) - hleda testy v zadanem adresari. Vychozi hodnota je aktualni adresar\n"
		."	--recursive - testy hleda i v podadresarich\n"	
		."	--parse-script=(file) - soubor obsahujici skript s parserem. Vychozi hodnota je parser.php v akutalnim adresari\n"	
		."	--int-script=(file) - soubor obsahujici skript s parserem. Vychozi hodnota je interpret.py v akutalnim adresari\n"	
		."	--parse-only - bude testovan pouze parser\n"	
		."	--int-only - bude testovan pouze interpret\n");
		exit(0);

	}elseif(strpos($argv[$i],"--directory=")===0){
		$dirname=substr($argv[$i], 12);
		if(!is_dir($dirname)){
			exit(11);
		}
	}elseif(strpos($argv[$i],"--parse-script=")===0){
		$parser=substr($argv[$i], 15);
		if(!is_file($parser)){
			exit(11);
		}
	}elseif(strpos($argv[$i],"--int-script=")===0){
		$interpret=substr($argv[$i], 13);
		if(!is_file($interpret)){
			exit(11);
		}
	}elseif($argv[$i]=="--recursive"){
		$recursive=True;
	}elseif($argv[$i]=="--parse-only"){
		if($intonly==False){
			$parseonly=True;
		}else{
			exit(10);
		}

	}elseif($argv[$i]=="--int-only"){
		if($parseonly==False){
			$intonly=True;
		}else{
			exit(10);
		}
	}else{
		exit(10);
	}
}
#pocitadla a seznamy uspesnych/neuspechnych testu
$failnute_testy=array();
$succes_testy=array();
$pocet_testu=0;
$failed_test=0;
$succes_test=0;

#testovani
test_finder($dirname);

#uprava hodnot pro HTML
$HTML_failnute_testy='';
$HTML_succes_testy='';
$failnute_testy_lastdir=$dirname;
$succes_testy_lastdirs=$dirname;

$dirname_part=explode("/",$dirname);
$dirname_part_len=sizeof($dirname_part);

if($failnute_testy){
	$HTML_failnute_testy.="<b>".$dirname."</b>\n";
	for($i=0;$i<sizeof($failnute_testy);$i++){
		$testname_part=explode("/",$failnute_testy[$i]);
		$testname=end($testname_part);
		$testname_part=array_slice($testname_part,$dirname_part_len);
		$testname_part = array_slice($testname_part, 0, sizeof($testname_part)-1);
		$testname_part = implode("/",$testname_part);

		if($testname_part!=$failnute_testy_lastdir){	
			$failnute_testy_lastdir=$testname_part;
			$HTML_failnute_testy.="\t\t<b>".$testname_part."</b>\n\n";
		}
		$HTML_failnute_testy.="\t\t\t".$testname."\n";

	}
}
if($succes_testy){
	$HTML_succes_testy.="<b>".$dirname."</b>\n";
	for($i=0;$i<sizeof($succes_testy);$i++){
		$testname_part=explode("/",$succes_testy[$i]);
		$testname=end($testname_part);
		$testname_part=array_slice($testname_part,$dirname_part_len);
		$testname_part = array_slice($testname_part, 0, sizeof($testname_part)-1);
		$testname_part = implode("/",$testname_part);

		if($testname_part!=$succes_testy_lastdir){	
			$succes_testy_lastdir=$testname_part;
			$HTML_succes_testy.="\t\t<b>".$testname_part."</b>\n\n";
		}
		$HTML_succes_testy.="\t\t\t".$testname."\n";

	}
}

#generovani HTML
print("<title lang=\"cz\">IPPcode19 testy</title>
	<head>
		<meta charset=\"utf-8\">
		<title>IPPcode19 test results</title>
		<meta name=\"Šimon Matyáš\">
		<style type=\"text/css\">
			.tg  {border-collapse:collapse;border-spacing:0;}
			.tg td{font-family:Arial, sans-serif;font-size:14px;padding:7px 20px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:black;}
			.tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:7px 20px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:black;}
			.tg .tg-yofg{background-color:#9aff99;text-align:left;vertical-align:top}
			.tg .tg-y6fn{background-color:#c0c0c0;text-align:left;vertical-align:top}
			.tg .tg-og4q{background-color:#fd6864;text-align:left;vertical-align:top}
		</style>
	</head>
	<body>
		<pre>
			<font size=\"48\">
			IPPcode19 Výsledky Testů
			</font>
		</pre>
		<table class=\"tg\" style=\"margin-left:200px;float:left;\">
		  <tr>
		    <th class=\"tg-y6fn\">Počet testů</th>
		    <th class=\"tg-y6fn\">$pocet_testu</th>
		  </tr>
		  <tr>
		    <td class=\"tg-yofg\">Úspěšné testy</td>
		    <td class=\"tg-yofg\">$succes_test</td>
		  </tr>
		  <tr>
		    <td class=\"tg-og4q\">Neúspěšné testy</td>
		    <td class=\"tg-og4q\">$failed_test</td>
		  </tr>
		</table>
		<pre style=\"margin-left:-25px;margin-top:-25px;float:left\">
                    <font size=\"5\" color=\"red\">
        <b>Seznam neúspěšných testů:</b>
        </font>$HTML_failnute_testy
		</pre>		
		<pre style=\"margin-left:50px;margin-top:-25px;float:left\">
                    <font size=\"5\" color=\"green\">
        <b>Seznam úspěšných testů:</b>
        </font>$HTML_succes_testy
		</pre>
	</body>
");





?>