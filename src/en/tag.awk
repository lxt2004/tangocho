BEGIN{ n=split(SPEC,parts,";"); for(i=1;i<=n;i++){ split(parts[i],kv,":"); cnt[i]=kv[1]; nm[i]=kv[2]; } ci=1; cum=0; bound=1; k=0 }
/^[VGS]\.push/{ k++; if(ci<=n && k==bound){ printf("_c=\"%s\";\n", nm[ci]); cum+=cnt[ci]; bound=cum+1; ci++ } }
{ print }
