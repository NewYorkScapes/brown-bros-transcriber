
function showMarkerArea(target) {
  const markerArea = new markerjs2.MarkerArea(target);
  markerArea.availableMarkerTypes = ['LineMarker'];
  markerArea.addRenderEventListener((imgURL, state) => {target.src = imgURL; imageSave = state;});
  markerArea.show();
  var strokeVals = imageSave['markers'];
  var all_vals = "";
  for(let i = 0; i < strokeVals.length; i++){
     var x1_val = JSON.stringify(strokeVals[i]['x1']);
     var y1_val = JSON.stringify(strokeVals[i]['y1']);
     var x2_val = JSON.stringify(strokeVals[i]['x2']);
     var y2_val = JSON.stringify(strokeVals[i]['y2']);
     var stroke = x1_val.concat('-',y1_val,'-',x2_val,'-',y2_val);
     all_vals = all_vals.concat(stroke, '|');
    }
  document.getElementById('segmentcoords').value = all_vals;
}