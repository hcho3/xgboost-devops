<?php
$metadata = parse_ini_file('./metadata.ini');

require '/var/www/aws/aws-autoloader.php';
use Aws\CloudWatch\CloudWatchClient;

$client = new CloudWatchClient([
  'region'  => 'us-west-2',
  'version' => 'latest'
]);

$result = $client->getMetricStatistics(array(
  'Namespace'  => 'XGBoostCICostWatcher',
  'MetricName' => 'TodayEC2SpendingUSD',
  'StartTime'  => strtotime('-48 hours'),
  'EndTime'    => strtotime('now'),
  'Period'     => 120,
  'Statistics' => array('Maximum')
));

$message = '';

function get_date($timestamp) {
  return explode('T', $timestamp)[0];
}

$data = $result['Datapoints'];
usort($data, function($a, $b) {
    if($a['Timestamp'] == $b['Timestamp']) {
        return 0;
    }
    return ($a['Timestamp'] < $b['Timestamp']) ? -1 : 1;
});
$prefix_max = 0;
$prev_timestamp = null;
foreach($data as $datapoint) {
  $timestamp[] = $datapoint['Timestamp'];
  if (!empty($prev_timestamp) && get_date($prev_timestamp) != get_date($datapoint['Timestamp'])) {
    $prefix_max = $datapoint['Maximum'];
  } else {
    $prefix_max = max($prefix_max, $datapoint['Maximum']);
  }
  $prev_timestamp = $datapoint['Timestamp'];
  $expense[] = $prefix_max;
}
?>
<html>
<head>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<script src="https://ajax.aspnetcdn.com/ajax/jQuery/jquery-3.5.0.min.js"></script>
<link rel="stylesheet"
href="https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,400;0,700;1,400;1,700&display=swap">
<style type="text/css">
#countdown_timer {
  font-size: 40pt;
  font-weight: bold;
}
#countdown_desc {
  font-size: 16pt;
}
body {
  font-family: 'Open Sans', sans-serif;
}
</style>
<script type="text/javascript">
function setMidnight() {
  // Set the date we're counting down to
  let midnight = new Date();
  midnight.setUTCHours(24,0,0,0);
  return midnight.getTime();
}

function zeroPad(x) {
  return ("00" + x).slice(-2);
}

function displayCountdown() {
  let now = new Date().getTime();
  let distance = countDownDate - now;
  let hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  let minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
  let seconds = Math.floor((distance % (1000 * 60)) / 1000);

  if (distance <= 0) {
    countDownDate = setMidnight();
  }
  $("#countdown_timer").html(zeroPad(hours) + ":" + zeroPad(minutes) + ":" + zeroPad(seconds));
}

let countDownDate = setMidnight();
$(document).ready(displayCountdown);
setInterval(displayCountdown, 1000);
</script>
</head>
<body>
<div id="graph_canvas"></div>
<div id="countdown_desc">
  Time left until the spending limit gets reset: <div id="countdown_timer"></div>
</div>
<script type="text/javascript">
let data = [
  {
    x: <?php echo("[\"" . implode("\",\"", $timestamp) . "\"]"); ?>,
    y: <?php echo("[" . implode(",", $expense) . "]"); ?>,
    type: 'scatter',
    name: 'TodayEC2SpendingUSD'
  },
  {
    x: <?php echo("[\"" . implode("\",\"", $timestamp) . "\"]"); ?>,
    y: <?php
      echo("[" . implode(",", array_fill(0, count($timestamp), $metadata['daily_budget'])) . "]");
    ?>,
    type: 'scatter',
    name: 'DailyBudget'
  }
];

let layout = {
  title: {
    text: 'Cloud expenses incurred since last midnight UTC'
  },
  xaxis: {
    title: {
      text: 'Time (UTC)'
    }
  },
  yaxis: {
    title: {
      text: 'USD'
    }
  },
  showlegend: true
};

Plotly.newPlot('graph_canvas', data, layout);
</script>
</body>
</html>
