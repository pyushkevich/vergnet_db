var listLabel=[];
var matchingProp=[];
	
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
	var url = window.location.href.toString();
	//var str = "builder";
	//if (url.includes(str)){
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
						var opmaj = document.createElement("option");
						opmaj.setAttribute("value",item);
						opmaj.appendChild(document.createTextNode(item));
						maj.appendChild(opmaj);
					});
				}
			},
			error: function(request, status, error) {
				console.log('error')
			}
		});
	//}	
}

function load_properties(id) {
	var sel = document.getElementById(id);
	var val = sel.options[sel.selectedIndex].value;
	var txt = sel.options[sel.selectedIndex].text;
	var varop = document.getElementById(id+"Op");
	for(i = varop.options.length-1; i>=0; i--){varop.remove(i);}
	if (val != "default"){
		jQuery.ajax({
			type:'post',
			url:'/temp/build_info/prop',
			cache:false,
			data: {"label": txt},
			success: function(answer) {
				if (answer != "[]"){
					temp = answer.split(", ");
					if (id=="major" && matchingProp.length>0){matchingProp=[];}
					for (x in temp){
						var prop = temp[x].replace(/\[/,'').replace(/\]/,'').replace(/\'/g,'');
						var opprop = document.createElement("option");
						opprop.setAttribute("value",prop);
						opprop.appendChild(document.createTextNode(prop));
						varop.appendChild(opprop);
						matchingProp.push(prop);
					}
					if (id!='major'){
						ltemp=[];
						matchingProp.forEach(function(element){
							ind = getAllIndexes(matchingProp, element);
							if (ind.length>1 && !ltemp.includes(element)){
								ltemp.push(element);
							}
						});
						matchingProp = ltemp;
						addMacthingProp(id, matchingProp);
					}
					//console.log(matchingProp)
				}
			},
			error: function(request, status, error){
				console.log('error')
			}
		});
		varop.hidden=false;
		document.getElementById("label"+id+"Op").hidden=false;
		document.getElementById(id+"criteria").hidden=false;
		/*document.getElementById("label"+id+"Crit").hidden=false;
		document.getElementById(id+"Crit").hidden=false;*/
	}
	else{
		varop.hidden=true;
		document.getElementById("label"+id+"Op").hidden=true;
		document.getElementById(id+"criteria").hidden=true;
		/*document.getElementById("label"+id+"Crit").hidden=true;
		document.getElementById(id+"Crit").hidden=true;*/
	}
	//if (id!="major") {addMacthingProp(id, matchingProp);}
}

function addMacthingProp(id, matchingProp){
	
	//var div = document.getElementById("builder_"+id);
	var div = document.getElementById(id+"criteria");
	var select = document.createElement("select");
	var label = document.createElement("label");
	var opdef = document.createElement("option");
	
	select.id="match"+id;
	select.name="match"+id;
	label.setAttribute('for', "match"+id); 
	label.innerHTML = "Choose how you want to match the two spreadsheets: ";
	opdef.setAttribute("value", "default");
	
	div.appendChild(document.createElement('br'));
	div.appendChild(label);
	div.appendChild(select);
	
	document.getElementById("match"+id).appendChild(opdef);
	for (i in matchingProp){
		var op = document.createElement("option");
		op.setAttribute("value", matchingProp[i]);
		op.innerHTML = matchingProp[i];
		document.getElementById("match"+id).appendChild(op);
	}
}	

function subButton(){
	var seloption = $('#majorOp option:selected').length;
	var button = document.getElementById("build");
	if (seloption>0){button.disabled=false;}
	else{button.disabled=true;}
}

function addOptional(){
	var div = document.createElement("div");
	var fields = document.getElementById("fieldBuilder");
	var buttonBuilder = document.getElementById("addcsv");
	var newSel = document.createElement("select");
	var newLabel = document.createElement("label");
	var newSelOp = document.createElement("select");
	var newLabelOp = document.createElement("label");
	var selName = "optional"+buttonBuilder.name;
	var defaultOp = document.createElement("option");
	var newCheckbox = document.createElement("input");
	var labelCheck = document.createElement("label");
	var deleteButton = document.createElement("button");
	
	defaultOp.value = "default";
 	defaultOp.appendChild(document.createTextNode("Choose a spreadsheet to link: "));
	newSel.id = selName;
	newSel.name = selName;
	newLabel.setAttribute("for",selName);
	newLabel.appendChild(document.createTextNode("Link this spreadsheet: "));
	newSelOp.id = selName+"Op";
	newSelOp.name = selName+"Op";
	newSelOp.multiple = true;
	newSelOp.hidden = true;
	newLabelOp.id = "label"+selName+"Op";
	newLabelOp.setAttribute("for", selName+"Op");
	newLabelOp.appendChild(document.createTextNode("Information to add: "));
	newLabelOp.hidden = true;
	newCheckbox.type = "checkbox";
	newCheckbox.name = "check"+selName;
	newCheckbox.id = "check"+selName;
	newCheckbox.checked = true;
	labelCheck.appendChild(newCheckbox);
	labelCheck.appendChild(document.createTextNode("Optional? "));
	div.id = "builder_"+selName;
	deleteButton.id = selName+"delBut"
	deleteButton.setAttribute("onclick", "deleteOptional(this.id)");
	deleteButton.innerHTML = "Delete optional ";
	deleteButton.type = "button";
	
	div.appendChild(document.createElement("br"));
	div.appendChild(labelCheck);
	div.appendChild(newLabel);
	div.appendChild(newSel);
	div.appendChild(newLabelOp);
	div.appendChild(newSelOp);
	div.appendChild(deleteButton);
	fields.appendChild(div);
	document.getElementById(selName).setAttribute("onchange", "load_properties(this.id); addCriteria(this.id)");
	document.getElementById(selName).appendChild(defaultOp);
	
	if (listLabel != "[]"){
		listLabel.forEach(function(item) {
			var newOp = document.createElement("option");
			newOp.setAttribute("value",item);
			newOp.appendChild(document.createTextNode(item));
			document.getElementById(selName).appendChild(newOp);
		});
	}	
	buttonBuilder.name=(parseInt(buttonBuilder.name)+1).toString();
	var divcrit = document.createElement("div");
	divcrit.id = selName+"criteria";
	divcrit.hidden = true;
	document.getElementById("builder_"+selName).appendChild(divcrit);
}

function addCriteria(id){
	var sel = document.getElementById(id);
	var val = sel.options[sel.selectedIndex].value;
	var txt = sel.options[sel.selectedIndex].text;
	var crit = document.getElementById(id+"criteria");
	var buttonBuilder = document.getElementById("addcsv");
	if (id.includes("major")){for (i = crit.childNodes.length-1; i>=6; i--){crit.removeChild(crit.childNodes[i]);};}
	else{for (i = crit.childNodes.length-1; i>=0; i--){crit.removeChild(crit.childNodes[i]);};}
	if (id.includes("major")){var opNum = "Maj"}
	else {var opNum = (parseInt(buttonBuilder.name)-1).toString()+"Op"};
	if (val != "default"){
		jQuery.ajax({
			type: 'post',
			url:'/temp/build_info/crit',
			cache: false,
			data: {"label": txt},
			success: function(answer) {
				if (answer != "([], [])"){
					answer=answer.replace(/{/g,"").replace(/}/g,"");
					l=answer.split("], [");
					lcrit=(l[0].replace(/\(/g,"").replace(/\[/g, "").replace(/\'/g,"")).split(", ");
					lchoicetemp=l[1].split("), (")
					lchoice=[]
					lchoicetemp.forEach(function(element){
						templist=(element.replace(/\(/g,"").replace(/\)/g,"").replace(/\[/g,"").replace(/\]/g,"").replace(/\'/g,"")).split(", ");
						lchoice.push(templist);
					});
									
					for (i=0; i<lcrit.length; i++){
						var label = document.createElement("label");
						var selectsign = document.createElement("select");
						var selectprop = document.createElement("select");					
						var opdef1 = document.createElement("option");
						var opdef2 = document.createElement("option");
						var opeq = document.createElement("option");
						var opdiff = document.createElement("option");
						
						ltemp=lcrit[i].replace(/\'/g,"")
						label.setAttribute("for", ltemp+"Crit"+opNum);
						label.innerHTML=ltemp+" criterion: "+ltemp+" ";
						selectsign.id = ltemp+"Crit"+opNum;
						selectsign.name = ltemp+"Crit"+opNum;
						selectprop.id = "val"+ltemp+"Crit"+opNum;
						selectprop.name = "val"+ltemp+"Crit"+opNum;
						opdef1.setAttribute("value","default");
						opdef2.setAttribute("value","default");
						opeq.setAttribute("value","=");
						opeq.innerHTML = "=";
						opdiff.setAttribute("value","<>");
						opdiff.innerHTML = "&ne;";
						
						selectsign.appendChild(opdef1);
						selectsign.appendChild(opeq);
						selectsign.appendChild(opdiff);
						selectprop.appendChild(opdef2);
						
						for (j in lchoice[i]){
							var optemp = document.createElement("option");
							optemp.value=j;
							optemp.innerHTML=lchoice[i][j];
							selectprop.appendChild(optemp);						
						}	
						
						if (crit.childNodes.length > 0){
							crit.appendChild(document.createElement("br"));
							crit.appendChild(document.createElement("br"));
						}
						crit.appendChild(label);
						crit.appendChild(selectsign);
						crit.appendChild(selectprop);
					}	
				}
			},
			error: function(request, status, error){
				console.log('error')
			}
		});
	}
}

function deleteOptional(id){
	var divid = "builder_"+id.replace('delBut','');
	var div = document.getElementById(divid);
	var buttonBuilder = document.getElementById("addcsv");
	div.parentNode.removeChild(div);
	buttonBuilder.name=(parseInt(buttonBuilder.name)-1).toString();
}