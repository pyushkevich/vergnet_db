var listLabel=[];
var matchingProp=["RID"];
	
function resetInput(){
	var input = document.getElementById("queryBuilder");
	input.value = ''
}
 
function getAllIndexes(arr, val) {
    var indexes = [], i;
    for(i = 0; i < arr.length; i++)
        if (arr[i] === val)
            indexes.push(i);
    return indexes;
}

function loadBuilderInfo(id){
	jQuery.ajax({
		type:'get',
		url:'/temp/build_info/label',
		cache:false,
		success: function(data) {
			temp = data.split(", ");
			for (x in temp){
				listLabel.push(temp[x].replace(/\[/,'').replace(/\]/,'').replace(/\'/g,''));
			}
			var maj = document.getElementById(id);
			
			if (listLabel != "[]"){
				listLabel.forEach(function(item) {
					var majop = document.createElement("option");
					majop.setAttribute("value",item);
					majop.innerHTML = item;
					maj.appendChild(majop);
				});
			}
		},
		error: function(request, status, error) {
			console.log('error')
		}
	});
}

function loadBuilderInfo_builder(){//id){
	jQuery.ajax({
		type:'get',
		url:'/temp/build_info/label',
		cache:false,
		success: function(data) {
			temp = data.split(", ");
			for (x in temp){
				listLabel.push(temp[x].replace(/\[/,'').replace(/\]/,'').replace(/\'/g,''));
			}
			var maj = document.getElementById('major');
			var op = document.getElementById('optional');
			if (listLabel != "[]"){
				listLabel.forEach(function(item) {
					if ((item != "DXSUM_PDXCONV_ADNIALL")  && (item != "PTDEMOG")){
						var majop = document.createElement("option");
						majop.setAttribute("value",item);
						majop.innerHTML = item;
						maj.appendChild(majop);
						
						var opop = document.createElement("option");
						opop.setAttribute("value",item);
						opop.innerHTML = item;
						op.appendChild(opop);
					}
				});
			}
		},
		error: function(request, status, error) {
			console.log('error')
		}
	});
}

function upload_maj(id) {
  var input = document.getElementById(id)
  var file = input.value;
  if (input.files && input.files.length===1)
  {
    var form_data = new FormData();
    var file = input.files[0];
    form_data.set("myfile", file , file.name);
    $.ajax({
      type: "POST",
      enctype: 'multipart/form-data',
      url: "/temp/build_info/upload",
      data: form_data,
      processData: false,
      contentType: false,
      cache: false,
      timeout: 600000,
      success: function(answer) {
        result = JSON.parse(answer);
        callback_maj(result, document.getElementById('majorOp'), result.label);
        document.getElementById("major").value = "default";
      }
    });
  }
}

function properties_maj(id, callback = callback_maj) {
	var sel = document.getElementById(id);
	var val = sel.options[sel.selectedIndex].value;
	var txt = sel.options[sel.selectedIndex].text;
	var varop = document.getElementById(id+"Op");
  console.log("VAROP", varop, id)
	
	selop = document.getElementById('optional');
	for (i = selop.options.length-1; i>=0; i--){selop.options[i].disabled = false;}

	for(i = varop.options.length-1; i>=0; i--){varop.remove(i);}
	if (val != "default"){
		jQuery.ajax({
			type:'post',
			url:'/temp/build_info/prop',
			cache:false,
			data: {"label": txt},
			success: function(answer) 
			{
				if (answer != "{}"){
					temp = JSON.parse(answer);
					callback(temp, varop, val);
          // Clear the file upload field
          if(id === "major") {
            document.getElementById("myfile").value = null;
          }
				}
			},
			error: function(request, status, error){console.log('error');}
		});
	}
}

function callback_maj(temp, varop, val){
	dates = temp["date"];
	viscodes = temp["viscode"];
	temp = temp["prop"]

  var length = varop.options.length;
  for (i = length-1; i >= 0; i--) {
    varop.options[i] = null;
  }

	for (x in temp){
		var prop = temp[x];
		var opprop = document.createElement("option");
		opprop.setAttribute("value",prop);
		opprop.innerHTML = prop;
		varop.appendChild(opprop);
	}

	var selector = 'span#spanoptional option[value=' + val + ']';
  var qsel = document.querySelector(selector);
  if(qsel)
    qsel.disabled = true;

  // Set the hidden input
  var majsel = document.getElementById('major_table');
  majsel.value = val;

	mergeOption(dates, viscodes);
}

function properties_opt(id, callback, valOp) {
	
	var val = valOp;
	var txt = valOp;
	var varop = document.getElementById(id);
		
	for(i = varop.options.length-1; i>=0; i--){varop.remove(i);}
	if (val != "default"){
		jQuery.ajax({
			type:'post',
			url:'/temp/build_info/prop',
			cache:false,
			data: {"label": txt},
			success: function(answer) {
				//if (answer != "[]"){
				if (answer != "{}"){
					temp = JSON.parse(answer);
					callback(temp, varop);
				}
			},
			error: function(request, status, error){
				console.log('error')
			}
		});
	}
}

function callback_opt(temp, varop){
	temp = temp["prop"]
	for (x in temp){
		var prop = temp[x];
		var opprop = document.createElement("option");
		opprop.setAttribute("value",prop);
		opprop.innerHTML = prop;
		varop.appendChild(opprop);
	}
}

function mergeOption(dates, viscodes){
	var datesel = document.getElementById('majdatesel');
	var viscodesel = document.getElementById('majviscodesel');
	
	for(i = datesel.options.length-1; i>=0; i--){datesel.remove(i);}
	for(i = viscodesel.options.length-1; i>=0; i--){viscodesel.remove(i);}

	for (date in dates){						
		var optemp = document.createElement("option");
		optemp.setAttribute("value",dates[date]);
		optemp.innerHTML = dates[date];
		datesel.appendChild(optemp);
	}
	for (viscode in viscodes){						
		var optemp = document.createElement("option");
		optemp.setAttribute("value",viscodes[viscode]);
		optemp.innerHTML = viscodes[viscode];
		viscodesel.appendChild(optemp);
	}
}	

function data_opt(id){
	var step2 = document.getElementById("step2");
	var step2_inner = document.getElementById("step2_inner");
	var step3_inner = document.getElementById("step3_inner");
	var values = $("#optional").val();

	if (step2_inner.childElementCount > 1){
		for(i = step2_inner.childElementCount-1; i>=1	; i--){
			step2_inner.children[i].remove();
		}
	}
	
	if (step3_inner.childElementCount > 0){
		for(i = step3_inner.childElementCount-1; i>=0; i--){
			step3_inner.children[i].remove();
		}
	}
	
	for (i in values){
		var spantemp2 = document.createElement("div");
		spantemp2.className="pure-u-1 pure-u-md-1-3";
		spantemp2.id = "spanoptional" + i + "Op";
		spantemp2.innerHTML = values[i] + ": <br>";
		
		var seltemp2 = document.createElement("select");
		seltemp2.id = "optional" + i + "Op";
		seltemp2.name = "optional" + i + "Op";
		seltemp2.setAttribute("onchange", "disable()");
		seltemp2.multiple = true;
		seltemp2.setAttribute("size", 10);
		
		var spantemp3 = document.createElement("div");
		spantemp3.className="pure-u-1 pure-u-md-1-2";
		spantemp3.id = "spanmerge" + i;
		spantemp3.innerHTML = "<b>" +  values[i] + ":</b><br>";
		
		var seltemp3 = document.createElement("select");
		seltemp3.id = "merge" + i;
		seltemp3.name = "merge" + i;
		seltemp3.setAttribute("data-table", values[i]);
		seltemp3.setAttribute("onchange","changeDefMerge(this.id); disable()");
		
		var opdef = document.createElement("option");
		opdef.setAttribute("value", "default");
		seltemp3.appendChild(opdef);
		
		var opDate = document.createElement("option");
		opDate.setAttribute("value", "date");
		opDate.innerHTML = "Date";
		seltemp3.appendChild(opDate);
		
		var opViscode = document.createElement("option");
		opViscode.setAttribute("value", "viscode");
		opViscode.innerHTML = "Viscode";
		seltemp3.appendChild(opViscode);

		// Extra fields in spantemp3
		var spantemp3_extras = document.createElement("div");
		spantemp3_extras.id = "extraspan_merge" + i;

		spantemp2.appendChild(seltemp2);
		spantemp2.appendChild(document.createElement("br"));
		var refstep2 = document.getElementById("step2previous");
		step2_inner.appendChild(spantemp2);
		// step2_inner.insertBefore(document.createElement("br"), refstep2);
		// step2_inner.insertBefore(document.createElement("br"), refstep2);
		properties_opt(seltemp2.id, callback_opt, values[i]);

		var seltemp3_label = document.createElement("label");
		seltemp3_label.control=seltemp3;
		seltemp3_label.innerHTML="Merge on:";

		spantemp3.appendChild(seltemp3_label);
		spantemp3.appendChild(seltemp3);
		spantemp3.appendChild(document.createElement("br"));
		spantemp3.appendChild(spantemp3_extras);

		document.getElementById("step3_inner").appendChild(spantemp3);

		var refstep3 = document.getElementById("step3previous");
		step3.insertBefore(document.createElement("br"), refstep3);
		step3.insertBefore(document.createElement("br"), refstep3);
	}
}

function changeDefMerge(id){
	var selmerge = document.getElementById(id);
	var spanmerge = document.getElementById("extraspan_"+id);
	var val = selmerge.value;
	var csvname = selmerge.getAttribute("data-table");
	
	var seltemp = document.createElement("select");
	seltemp.id = "custom" + id;
	seltemp.name = "custom" + id;

	var seltemp_label = document.createElement("label");
	seltemp_label.control = seltemp.id;

	if (spanmerge.childElementCount > 0){
	  for(i = spanmerge.childElementCount-1; i>=0; i--) {spanmerge.children[i].remove();}
	}
	
	if (val != "default"){
		if (val == "date") {d = {"csvname":csvname, "type":"date"};}
		else if (val == "viscode") {d = {"csvname":csvname, "type":"viscode"};}
		
		jQuery.ajax({
			type:'post',
			url:'/temp/build_info/opvar',
			cache:false,
			data:d,
			success: function(answer) {
				if (answer != "[]"){
					temp = JSON.parse(answer);
					for (i in temp){
						var optemp = document.createElement("option");
						optemp.setAttribute("value",temp[i]);
						optemp.innerHTML = temp[i];
						seltemp.appendChild(optemp);
					}
					spanmerge.appendChild(seltemp_label);
					spanmerge.appendChild(seltemp);
					spanmerge.appendChild(document.createElement("br"));

					if (val == "date"){

						seltemp_label.innerHTML = "Date field:";

						var seldate = document.createElement("select");
						seldate.id = "date" + seltemp.id;
						seldate.name = seldate.id;
						
						var seldate_label = document.createElement("label");
						seldate_label.control = seldate.id;
						seldate_label.innerHTML = "Match type:"

						var opeq = document.createElement("option");
						opeq.setAttribute("value", "equal");
						opeq.innerHTML = "Equal";
						
						var opclo = document.createElement("option");
						opclo.setAttribute("value", "closest");
						opclo.innerHTML = "Closest";

						var opbef = document.createElement("option");
						opbef.setAttribute("value", "before");
						opbef.innerHTML = "Closest before";
						
						var opaft = document.createElement("option");
						opaft.setAttribute("value", "after");
						opaft.innerHTML = "Closest after";

						seldate.appendChild(opeq);
						seldate.appendChild(opclo);
						seldate.appendChild(opbef);
						seldate.appendChild(opaft);

						seldate.setAttribute("onchange","onDateMatchChange(this.id)");

						// Create a span for the range sub-option
						var spandaterange = document.createElement("span");
						spandaterange.id = "range"+seldate.id;

						spanmerge.appendChild(seldate_label);
						spanmerge.appendChild(seldate);
						spanmerge.appendChild(document.createElement("br"));
						spanmerge.appendChild(spandaterange);
					}
					else {
						seltemp_label.innerHTML = "Visit code field:";
					}

					// Add the hard/soft join option
					var seljoin = document.createElement("select");
					seljoin.id = "jointype" + seltemp.id;
					seljoin.name = seljoin.id;

					var seljoin_label = document.createElement("label");
					seljoin_label.control = seljoin.id;
					seljoin_label.innerHTML = "Join type:"

					var opleft = document.createElement("option");
					opleft.setAttribute("value", "left");
					opleft.innerHTML = "Left Join";

					var opfull = document.createElement("option");
					opfull.setAttribute("value", "full");
					opfull.innerHTML = "Full Join";

					seljoin.appendChild(opleft);
					seljoin.appendChild(opfull);

					spanmerge.appendChild(seljoin_label);
					spanmerge.appendChild(seljoin);

				}else{
					for (i = 0; i < selmerge.length; i++){
						if (selmerge.options[i].value == val){selmerge.remove(i);}
					}
				}
			},
			error: function(request, status, error) {
				console.log('error');
			}
		});
	}
}

function onDateMatchChange(id) {
	var seldate = document.getElementById(id);

	var spandaterange = document.getElementById("range"+id);
	while (spandaterange.childElementCount > 0)
		spandaterange.children[spandaterange.childElementCount-1].remove();

	if(seldate.value === "closest") {
		var datefrom = document.createElement("input");
		datefrom.name = datefrom.id = "fromdate_" + id;
		datefrom.value = -180;

		var datefrom_label = document.createElement("label");
		datefrom_label.control = datefrom.id;
		datefrom_label.innerHTML = "Lower bound (days): ";

		var dateto = document.createElement("input");
		dateto.name = datefrom.id = "todate_" + id;
		dateto.value = 180;

		var dateto_label = document.createElement("label");
		dateto_label.control = dateto.id;
		dateto_label.innerHTML = "Upper bound (days): ";

		spandaterange.appendChild(datefrom_label);
		spandaterange.appendChild(datefrom);
		spandaterange.appendChild(document.createElement("br"));
		spandaterange.appendChild(dateto_label);
		spandaterange.appendChild(dateto);
		spandaterange.appendChild(document.createElement("br"));
	}
}

function subButton(){
	var seloption = $('#majorOp option:selected').length;
	var button = document.getElementById("build");
	if (seloption>0){button.disabled=false;}
	else{button.disabled=true;}
}
