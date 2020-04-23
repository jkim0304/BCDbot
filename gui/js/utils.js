function encode(name){ 
	name = name.replace(/\(/g, '_leftparens_');
	name = name.replace(/\)/g, '_rightparens_');
	name = name.replace(/:/g, '_colon_');
	name = name.replace(/'/g, '_apostrophe_');
	return name.replace(/ /g,'_spacehere_'); 
}

function unencode(sid){ 
	sid = sid.replace(/_leftparens_/g, '(');
	sid = sid.replace(/_rightparens_/g, ')');
	sid = sid.replace(/_colon_/g, ':');
	sid = sid.replace(/_apostrophe_/g, '\'');
	return sid.replace(/_spacehere_/g, ' '); 
}

function sortdb(db) { db.sort(function(a,b){ 
	return b[1]['max_clump_scores']-a[1]['max_clump_scores']; }); 
}

function arraysEqual(_arr1, _arr2) {
    if (!Array.isArray(_arr1) || ! Array.isArray(_arr2) || _arr1.length !== _arr2.length)
      return false;
   
    var arr1 = _arr1.concat().sort();
    var arr2 = _arr2.concat().sort();

    for (var i = 0; i < arr1.length; i++) {
        if (arr1[i] !== arr2[i])
            return false;
    }
    return true;
}

function checkSeen(already_seen, cards) {
	for(var j = 0; j < already_seen.length; j++) {
		if(arraysEqual(already_seen[j],cards)){
			return true;
		}
	}
	return false;
}

function ignoreSubclumps(clumps){
	clumps.sort(function(a,b){
		return b[0].length-a[0].length;
	});
	for(var i = 0; i < clumps.length; i++) {
		for(var j = clumps.length-1; j > 0; j--){
			if(clumps[i]==clumps[j]){
				break;
			}
			var subset = true;
			//console.log(clumps[j])
			for(var c = 0; c < clumps[j][0].length; c++) {
				if(!clumps[i][0].includes(clumps[j][0][c])){
					subset = false;
				}
			}
			if(subset == true) {	
				clumps.splice(j,1);
			}

		}
		
	}
	return clumps;

}