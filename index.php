<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Similarity Search</title>
  <style>
    :root{
      --bg: #010101;
      --primary: #b6895b;
      --text: #ffffff;
    }

    body{
      background-color: var(--bg);
      color: var(--text);
      font-family: sans-serif;
      padding: 2rem;
    }

    button{
      background-color: var(--primary);
      color: black;
      padding: 0.6rem 1.2rem;
      margin-bottom: 1rem;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 600;
    }

    button:hover{ 
      background-color: #9c7c50; 
    }

    label{ 
      font-weight: 500; 
      margin-right: 0.5rem; 
    }

    input[type="text"], select{
      padding: 0.4rem 0.6rem;
      border: 1px solid #333333;
      border-radius: 4px;
      background-color: #222222; 
      color: var(--text);
      margin-right: 0.5rem;
    }

    input[type="checkbox"]{
      margin: 0 0.2rem 0 1rem;
      transform: scale(1.2);
      cursor: pointer;
    }

    table{
      border-collapse: collapse;
      margin-top: 1rem;
      width: 100%;
    }

    table, th, td{
      border: 1px solid #333333;
    }

    thead th{
      background-color: var(--primary);
      color: black;
      font-weight: 600;
    }

    th, td{ 
      padding: 0.6rem;
      vertical-align: top;
      text-align: left;
    }
  </style>
</head>
<body>
  <h1>Similarity Search for Twitter, YouTube & Instagram</h1><br>

  <form method="POST">
    <p>
      <label for="keyword">Enter Keyword:</label>
      <input type="text" id="keyword" name="keyword" required>
    </p>
    <p>
      <label for="source">Choose Source: </label>
      <input type="checkbox" id="twitter" name="source[]" value="twitter"> Twitter
      <input type="checkbox" id="youtube" name="source[]" value="youtube"> YouTube
      <input type="checkbox" id="instagram" name="source[]" value="instagram"> Instagram
    </p>
    <p>
      <label for="metric">Choose Metric:</label>
      <select id="metric" name="metric">
        <option value="dice">Dice</option>
        <option value="jaccard">Jaccard</option>
      </select>
    </p>
    <button type="submit" name="submit">Submit</button>
  </form>

  <?php
  if (isset($_POST['submit'])) {
      set_time_limit(420);

      $keyword = escapeshellarg($_POST['keyword']);
      $metric = escapeshellarg($_POST['metric']);
      $sources = isset($_POST['source']) ? $_POST['source'] : [];

      if (empty($sources)) {
          echo "<p>Error: Pilih setidaknya satu sumber (Twitter, YouTube, atau Instagram).</p>";
          exit;
      }

      $source_args = implode(' ', array_map('escapeshellarg', $sources));

      $command = "python process.py $keyword $source_args $metric 2>&1";
      $output = shell_exec($command);

      echo "<h2>Hasil Similarity:</h2><br>";

      $lines = explode("\n", $output);

      $results = [];
      $current = [
        'source'       => '',
        'original'     => '',
        'preprocessed' => '',
        'score'        => ''
      ];
      $current_section = null;

      foreach ($lines as $line) {
          $trimmed = trim($line);

          if (strpos($trimmed, '-----') === 0) {
              if (!empty($current['source'])) {
                  $results[] = $current;
              }
              $current = [
                'source'       => '',
                'original'     => '',
                'preprocessed' => '',
                'score'        => ''
              ];
              $current_section = null;
              continue;
          }

          if ($trimmed === '') { 
              continue; 
          }

          if (strpos($trimmed, 'Source: ') === 0) {
              $current['source'] = substr($trimmed, 8);
              $current_section = null;
          }
          else if (strpos($trimmed, 'Original Text: ') === 0) {
              $current['original'] = substr($trimmed, 15);
              $current_section = 'original';  
          }
          else if (strpos($trimmed, 'Preprocessed Text: ') === 0) {
              $current['preprocessed'] = substr($trimmed, 19);
              $current_section = 'preprocessed';
          }
          else if (strpos($trimmed, 'Similarity Score: ') === 0) {
              $current['score'] = substr($trimmed, 17);
              $current_section = null;
          }
          else {
              if ($current_section === 'original') {
                  $current['original'] .= "\n" . $trimmed; 
              } 
              else if ($current_section === 'preprocessed') {
                  $current['preprocessed'] .= "\n" . $trimmed;
              }
          }
      }
      if (!empty($current['source'])) {
          $results[] = $current;
      }

      if (!empty($results)) {
          echo '<table>';
          echo '<thead>
                  <tr>
                      <th>Source</th>
                      <th>Original Text</th>
                      <th>Preprocessed Text</th>
                      <th>Similarity Score</th>
                  </tr>
                </thead>
                <tbody>';

          foreach ($results as $res) {
              $original_text = nl2br(htmlspecialchars($res['original']));
              $preprocessed_text = nl2br(htmlspecialchars($res['preprocessed']));
              $similarity_score = htmlspecialchars($res['score']);
              $source = htmlspecialchars($res['source']);

              echo '<tr>';
              echo "<td>$source</td>";
              echo "<td style='max-width: 400px; white-space: pre-wrap;'>$original_text</td>";
              echo "<td style='max-width: 400px; white-space: pre-wrap;'>$preprocessed_text</td>";
              echo "<td>$similarity_score</td>";
              echo '</tr>';
          }

          echo '</tbody></table>';
      }
  }
  ?>
</body>
</html>
