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
  'Period'     => 900,
  'Statistics' => array('Maximum')
));

$message = '';

$data = $result['Datapoints'];
usort($data, function($a, $b) {
    if($a['Timestamp'] == $b['Timestamp']) {
        return 0;
    }
    return ($a['Timestamp'] < $b['Timestamp']) ? -1 : 1;
});
foreach($data as $datapoint) {
  $timestamp[] = $datapoint['Timestamp'];
  $expense[] = $datapoint['Maximum'];
}
?>
<html>
<head>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
<div id='myDiv'></div>
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
  showlegend: true,
  legend: {
    x: 1,
    xanchor: 'right',
    y: 1
  }
};

Plotly.newPlot('myDiv', data, layout);
</script>
</body>
</html>
