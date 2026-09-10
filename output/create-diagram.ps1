Add-Type -AssemblyName System.Drawing
$outDir = $PSScriptRoot
$width = 5000
$height = 1000
$bitmap = New-Object System.Drawing.Bitmap($width, $height)
$bitmap.SetResolution(300, 300)
$g = [System.Drawing.Graphics]::FromImage($bitmap)
$g.Clear([System.Drawing.Color]::White)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$svg = [System.Collections.Generic.List[string]]::new()
$svg.Add('<svg xmlns="http://www.w3.org/2000/svg" width="5000" height="1000" viewBox="0 0 5000 1000"><title>AI简历诊断与岗位匹配系统用例图</title><rect width="5000" height="1000" fill="white"/>')
$gray = '#ADB3BA'
$green = '#71CDB0'
$ink = '#33383D'
function Rect($x,$y,$w,$h,$color,$strokeWidth) {
  $pen = [System.Drawing.Pen]::new([System.Drawing.ColorTranslator]::FromHtml($color),$strokeWidth)
  $g.FillRectangle([System.Drawing.Brushes]::White,[single]$x,[single]$y,[single]$w,[single]$h)
  $g.DrawRectangle($pen,[single]$x,[single]$y,[single]$w,[single]$h)
  $svg.Add("<rect x='$x' y='$y' width='$w' height='$h' fill='white' stroke='$color' stroke-width='$strokeWidth'/>")
  $pen.Dispose()
}
function Text($x,$y,$label,$size) {
  $font = [System.Drawing.Font]::new('Microsoft YaHei',[single]$size,[System.Drawing.FontStyle]::Regular,[System.Drawing.GraphicsUnit]::Pixel)
  $format = [System.Drawing.StringFormat]::new()
  $format.Alignment = [System.Drawing.StringAlignment]::Center
  $format.LineAlignment = [System.Drawing.StringAlignment]::Center
  $brush = [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml($ink))
  $g.DrawString($label,$font,$brush,[System.Drawing.PointF]::new($x,$y),$format)
  $safe = [System.Security.SecurityElement]::Escape($label)
  $svg.Add("<text x='$x' y='$y' text-anchor='middle' dominant-baseline='central' font-family='Microsoft YaHei, Noto Sans CJK SC, sans-serif' font-size='$size' fill='$ink'>$safe</text>")
  $font.Dispose(); $format.Dispose(); $brush.Dispose()
}
function Line($coords) {
  $pen = [System.Drawing.Pen]::new([System.Drawing.ColorTranslator]::FromHtml($gray),1.8)
  $points = [System.Collections.Generic.List[System.Drawing.PointF]]::new()
  $pairs = @()
  for($i=0;$i -lt $coords.Count;$i+=2) {
    $points.Add([System.Drawing.PointF]::new($coords[$i],$coords[$i+1]))
    $pairs += "$($coords[$i]),$($coords[$i+1])"
  }
  $g.DrawLines($pen,$points.ToArray())
  $svg.Add("<polyline points='$($pairs -join ' ')' fill='none' stroke='$gray' stroke-width='1.8'/>")
  $pen.Dispose()
}
function Node($x,$y,$lines,$size=29) {
  Rect ($x-140) $y 280 104 $green 2
  $arr = $lines -split '\|'
  $lineHeight = 33
  $start = $y+52-(($arr.Count-1)*$lineHeight/2)
  for($k=0;$k -lt $arr.Count;$k++) { Text $x ($start+$k*$lineHeight) $arr[$k] $size }
}
Text 2500 56 'AI简历诊断与岗位匹配系统用例图' 44
Rect 52 116 4896 216 $gray 2
Rect 52 416 4896 216 $gray 2
Rect 52 716 4896 216 $gray 2
$centers = @(0..14 | ForEach-Object {232+324*$_})
$groups = @(
  @{label='简历管理'; indexes=@(0,1,2)},
  @{label='JD管理'; indexes=@(3,4)},
  @{label='智能匹配分析'; indexes=@(5,6,7)},
  @{label='Gap分析'; indexes=@(8,9,10)},
  @{label='简历优化'; indexes=@(11,12)},
  @{label='结果与历史管理'; indexes=@(13,14)}
)
$ops = @('上传PDF简历','粘贴简历文本','查看解析结果','输入JD','管理JD','发起岗位匹配','查看匹配分数','查看技能匹配','查看已匹配能力','查看表达Gap','查看技能Gap','获取定向|优化建议','AI优化简历','查看历史记录','重新进行|匹配分析')
$responses = @('解析简历内容','结构化展示|简历信息','提取岗位|核心要求','保存并展示|JD列表','执行简历与|JD匹配','展示总体|匹配程度','展示岗位要求与|简历证据|对应关系','展示已有充分|证据的能力','识别已有能力但|表达不足的内容','识别缺少真实|证据的技能或经历','生成JD定向|修改建议','生成STAR式|优化内容','展示历史|匹配结果','对修改后的简历|重新分析')
# Draw connectors before nodes. Route the center column around the row labels.
foreach($group in $groups) {
  $idx = $group.indexes
  $cx = ($centers[$idx[0]]+$centers[$idx[-1]])/2
  Line @($cx,284,$cx,368)
  Line @($centers[$idx[0]],368,$centers[$idx[-1]],368)
  foreach($i in $idx) {
    $x = $centers[$i]
    if($i -eq 7) { Line @($x,368,$x,402,2600,402,2600,470,$x,470,$x,486) }
    else { Line @($x,368,$x,486) }
  }
}
Line @($centers[0],590,$centers[0],671,394,671)
Line @($centers[1],590,$centers[1],671,394,671)
Line @(394,671,394,786)
for($i=2;$i -lt 15;$i++) {
  $x = $centers[$i]
  if($i -eq 7) { Line @($x,590,$x,702,2600,702,2600,770,$x,770,$x,786) }
  else { Line @($x,590,$x,786) }
}
Text 2500 146 '系统功能' 28
Text 2500 446 '用户操作' 28
Text 2500 746 '系统响应' 28
foreach($group in $groups) {
  $idx = $group.indexes
  $cx = ($centers[$idx[0]]+$centers[$idx[-1]])/2
  Node $cx 180 $group.label
}
for($i=0;$i -lt 15;$i++) { Node $centers[$i] 486 $ops[$i] }
Node 394 786 $responses[0] 28
for($i=1;$i -lt 14;$i++) { Node $centers[$i+1] 786 $responses[$i] 28 }
$svg.Add('</svg>')
$svgPath = Join-Path $outDir 'AI简历诊断与岗位匹配系统用例图.svg'
$pngPath = Join-Path $outDir 'AI简历诊断与岗位匹配系统用例图.png'
[System.IO.File]::WriteAllLines($svgPath,$svg,[System.Text.UTF8Encoding]::new($false))
$bitmap.Save($pngPath,[System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bitmap.Dispose()
Write-Output $pngPath
Write-Output $svgPath
