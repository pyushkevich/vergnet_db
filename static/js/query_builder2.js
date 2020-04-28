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

function properties_maj(id, callback = callback_maj) {
	var sel = document.getElementById(id);
	var val = sel.options[sel.selectedIndex].value;
	var txt = sel.options[sel.selectedIndex].text;
	var varop = document.getElementById(id+"Op");
	
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
					/* dates = temp["date"];
					viscodes = temp["viscode"];
					temp = temp["prop"]
					
					for (x in temp){
						var prop = temp[x];
						var opprop = document.createElement("option");
						opprop.setAttribute("value",prop);
						opprop.innerHTML = prop;
						varop.appendChild(opprop);
					}
					
					var selector = 'span#spanoptional option[value=' + val + ']';
					document.querySelector(selector).disabled = true;
					mergeOption(dates, viscodes); */
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

	for (x in temp){
		var prop = temp[x];
		var opprop = document.createElement("option");
		opprop.setAttribute("value",prop);
		opprop.innerHTML = prop;
		varop.appendChild(opprop);
	}

	var selector = 'span#spanoptional option[value=' + val + ']';
	document.querySelector(selector).disabled = true;
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
	var step3 = document.getElementById("step3");
	var values = $("#optional").val();

	if (step2.childElementCount > 3){
		for(i = step2.childElementCount-3; i>=3; i--){
			step2.children[i].remove();
		}
	}
	
	if (step3.childElementCount > 3){
		for(i = step3.childElementCount-3; i>=3; i--){
			step3.children[i].remove();
		}
	}
	
	for (i in values){
		var spantemp2 = document.createElement("span");
		spantemp2.id = "spanoptional" + i + "Op";
		spantemp2.innerHTML = values[i] + ": ";
		
		var seltemp2 = document.createElement("select");
		seltemp2.id = "optional" + i + "Op";
		seltemp2.name = "optional" + i + "Op";
		seltemp2.setAttribute("onchange", "disable()");
		seltemp2.multiple = true;
		
		var spantemp3 = document.createElement("span");
		spantemp3.id = "spanmerge" + i;
		spantemp3.innerHTML = values[i] + " how to merge: ";
		
		var seltemp3 = document.createElement("select");
		seltemp3.id = "merge" + i;
		seltemp3.name = "merge" + i;
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
		
		
		spantemp2.appendChild(seltemp2);
		var refstep2 = document.getElementById("step2previous");
		step2.insertBefore(spantemp2, refstep2);
		step2.insertBefore(document.createElement("br"), refstep2);
		step2.insertBefore(document.createElement("br"), refstep2);
		properties_opt(seltemp2.id, callback_opt, values[i]);
		
		spantemp3.appendChild(seltemp3);
		var refstep3 = document.getElementById("step3previous");
		step3.insertBefore(spantemp3, refstep3);
		step3.insertBefore(document.createElement("br"), refstep3);
		step3.insertBefore(document.createElement("br"), refstep3);
	}
}

function changeDefMerge(id){
	var selmerge = document.getElementById(id);
	var spanmerge = document.getElementById("span"+id);
	var val = selmerge.value;
	var csvname = (spanmerge.innerHTML).split(" ")[0];
	
	var seltemp = document.createElement("select");
	seltemp.id = "custom" + id;
	seltemp.name = "custom" + id;
	
	if (spanmerge.childElementCount > 1){
		for(i = spanmerge.childElementCount-1; i>=1; i--) {spanmerge.children[i].remove();}
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
					spanmerge.appendChild(seltemp);
					
					if (val == "date"){
						var seldate = document.createElement("select");
						seldate.id = "date" + seltemp.id;
						seldate.name = seldate.id;
						
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
						
						spanmerge.appendChild(seldate);
					}
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

function subButton(){
	var seloption = $('#majorOp option:selected').length;
	var button = document.getElementById("build");
	if (seloption>0){button.disabled=false;}
	else{button.disabled=true;}
}