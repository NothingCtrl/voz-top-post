<?php

$files = array_diff(scandir('.'), array('.', '..'));

if (!empty($files)) {
    rsort($files);
    echo "<html><head><meta charset='UTF-8'>
<title>VOZ TOP</title>
<style type='text/css'>
    body {font-size: 14px; font-family: Arial, Helvetica, Sans-serif, serif;}
    ol {padding-bottom: 14px;}
    li {padding-bottom: 10px;}
    a {text-decoration:none;}
</style>

</head><body>
<h1>VOZ TOP</h1>
<ol>";
    foreach ($files as $file) {
        if (strpos($file, 'voz_') !== false) {
            $name = str_replace('.html', '', $file);
            $tmp = explode('_', $name);
            $str_date = end($tmp);
            $name = str_replace("_" . $str_date, '', $name);
            $name = str_replace("_", ' ', $name);
            $name = ucwords($name);
            $date = date_create_from_format("Y-m-d-H-i", $str_date);
            $vn_time_zone = new DateTimeZone('Asia/Ho_Chi_Minh');
            $date->setTimezone($vn_time_zone);
            $str_date = $date->format("Y-m-d H:i");
            echo "<li><a href='{$file}'>{$name} / {$str_date}</a></li>";
        }
    }
    echo "</ol></body></html>";
}
