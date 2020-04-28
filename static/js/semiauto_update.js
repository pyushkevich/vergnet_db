function loadForm(){
	var url = window.location.href.toString();
	var str = "dl_spreadsheet";
	if (url.includes(str)){
		jQuery.ajax({
			type:'get',
			url:'/temp/dl_spreadsheet/',
			cache:false,
			success:function(data){
				var csvfiles=data.replace(/\[|\]|'/g,"").split(",");
				var x;
				var fieldlist=document.getElementById("field-sa");
				for (x in csvfiles){
					var csvname = csvfiles[x].trim().replace('.csv',"");
					if (x==0){var csv = ' '+csvfiles[x];}
					else {var csv = csvfiles[x];}
					var div = document.createElement("div");
					var input = document.createElement("input");
					var label = document.createElement("label");
					input.type = "checkbox";
					input.id = csvname;
					input.name = "saupdate";
					input.value = csvname;
					input.classList.add("checkbox-sa");
					input.checked = true;
					label.htmlFor = csvname;
					label.appendChild(document.createTextNode(csv));
					div.appendChild(input);
					div.appendChild(label);
					fieldlist.appendChild(div);
				}
			},
			error: function(request, status, error){
				console.log('error')
			}
		});
	}
}

function selectAll(){
	var formsa = document.getElementById("field-sa");
	var fields = formsa.querySelectorAll(".checkbox-sa");
	length = fields.length;
	for (var i = 0; i<length; i++){
		var field=fields[i];
		if (!field.checked){field.checked=true;}
	}	
}

function unselectAll(){
	var formsa = document.getElementById("field-sa");
	var fields = formsa.querySelectorAll(".checkbox-sa");
	length = fields.length;
	for (var i = 0; i<length; i++){
		var field=fields[i];
		if (field.checked){field.checked=false;}
	}	
}