<?php
require '../../composer/vendor/autoload.php';

use Aws\CloudWatch\CloudWatchClient;

$client = new CloudWatchClient([
    'region' => 'us-west-2',
    'version' => 'latest'
]);

$start_time = strtotime('-48 hours');
$end_time = strtotime('now');
$expense_metric = $client->getMetricStatistics(array(
    'Namespace' => 'XGBoostCICostWatcher',
    'MetricName' => 'TodayEC2SpendingUSD',
    'StartTime' => $start_time,
    'EndTime' => $end_time,
    'Period' => 60,
    'Statistics' => array('Maximum')
));
$budget_metric = $client->getMetricStatistics(array(
    'Namespace' => 'XGBoostCICostWatcher',
    'MetricName' => 'DailyBudgetUSD',
    'StartTime' => $start_time,
    'EndTime' => $end_time,
    'Period' => 60,
    'Statistics' => array('Maximum')
));

$message = '';

function get_date($timestamp) {
  return explode('T', $timestamp)[0];
}

function sort_by_timestamp($a, $b) {
  if ($a['Timestamp'] == $b['Timestamp']) {
    return 0;
  }
  return ($a['Timestamp'] < $b['Timestamp']) ? -1 : 1;
}

$expense_data = $expense_metric['Datapoints'];
usort($expense_data, "sort_by_timestamp");
$prefix_max = 0;
foreach ($expense_data as $datapoint) {
  $expense_timestamp[] = $datapoint['Timestamp'];
  $expense_value[] = $datapoint['Maximum'];
}

$budget_data = $budget_metric['Datapoints'];
usort($budget_data, "sort_by_timestamp");
foreach ($budget_data as $datapoint) {
  $budget_timestamp[] = $datapoint['Timestamp'];
  $budget_value[] = $datapoint['Maximum'];
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
    x: <?php echo("[\"" . implode("\",\"", $expense_timestamp) . "\"]"); ?>,
    y: <?php echo("[" . implode(",", $expense_value) . "]"); ?>,
    type: 'scatter',
    name: 'TodayEC2SpendingUSD'
  },
  {
    x: <?php echo("[\"" . implode("\",\"", $budget_timestamp) . "\"]"); ?>,
    y: <?php echo("[" . implode(",", $budget_value) . "]"); ?>,
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
