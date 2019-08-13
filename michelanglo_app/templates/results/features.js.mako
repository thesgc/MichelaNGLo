

### copied from results.js.mako in VENUS
###################################################
window.ft = new FeatureViewer('${protein.sequence}',
           '#fv',
            {
                showAxis: true,
                showSequence: true,
                brushActive: true, //zoom
                toolbar:true, //current zoom & mouse position
                bubbleHelp:false,
                zoomMax:50 //define the maximum range of the zoom
            });

################### Own SNV #######################
## DISABLED.

################### Domains #######################
%if 'domain' in protein.features:
    ft.addFeature({
        data: ${str(protein.features['domain'])|n},
        name: "Domain",
        className: "domain",
        color: "lightblue",
        type: "rect",
        filter: "Domain"
    });
%endif

<%
    combo_roi=[]
    for key in ('transmembrane region','intramembrane region','region of interest','peptide','site','active site','binding site','calcium-binding region','zinc finger region','metal ion-binding site','DNA-binding region','lipid moiety-binding region', 'nucleotide phosphate-binding region'):
        if key in protein.features:
            combo_roi.extend(protein.features[key])

    combo_other=[]
    for key in ('propeptide','signal peptide','repeat','coiled-coil region','compositionally biased region','short sequence motif','topological domain','transit peptide'):
        if key in protein.features:
            combo_other.extend(protein.features[key])

    combo_ptm=[]
    for key in ('initiator methionine','modified residue','glycosylation site','non-standard amino acid'):
        if key in protein.features:
            combo_ptm.extend(protein.features[key])

    combo_ss=[]
    for key in ('helix', 'turn', 'strand'):
        if key in protein.features:
            combo_ss.extend(protein.features[key])
%>
%if combo_roi:
    ft.addFeature({
        data: ${str(combo_roi)|n},
        name: "region of interest",
        className: "domain",
        color: "teal",
        type: "rect",
        filter: "Domain"
    });
%endif

%if combo_other:
    ft.addFeature({
        data: ${str(combo_other)|n},
        name: "other regions",
        className: "domain",
        color: "lavender",
        type: "rect",
        filter: "Domain"
    });
%endif

%if combo_ptm:
    ft.addFeature({
        data: ${str(combo_ptm)|n},
        name: "Modified residues",
        className: "modified",
        color: "slateblue",
        type: "unique",
        filter: "Modified"
    });
%endif

%if combo_ss:
    ft.addFeature({
        data: ${str(combo_ss)|n},
        name: "Secondary structure",
        className: "domain",
        color: "olive",
        type: "rectangle",
        filter: "Domain"
    });
%endif



%if 'sequence variant' in protein.features:
    ft.addFeature({
        data: ${str(protein.features['sequence variant'])|n},
        name: "seq. variant",
        className: "modified",
        color: "firebrick",
        type: "unique",
        filter: "Modified"
    });
%endif

%if 'splice variant' in protein.features:
    ft.addFeature({
        data: ${str(protein.features['splice variant'])|n},
        name: "splice variant",
        className: "domain",
        color: "sandybrown",
        type: "rectangle",
        filter: "Domain"
    });
%endif

%if protein.gNOMAD:
    ft.addFeature({
        data: ${str(protein.gNOMAD)|n},
        name: "gNOMAD",
        className: "modified",
        color: "skyblue",
        type: "unique",
        filter: "Modified"
    });
%endif

%if 'disulfide bond' in protein.features:
    ft.addFeature({
        data: ${str(protein.features['disulfide bond'])|n},
        name: "disulfide bond",
        className: "dsB",
        color: "orange",
        type: "path",
        filter: "Modified Residue"
    });
%endif

%if 'cross-link' in protein.features:
    ft.addFeature({
        data: ${str(protein.features['cross-link'])|n},
        name: "disulfide bond",
        className: "dsB",
        color: "orange",
        type: "path",
        filter: "Modified Residue"
    });
%endif

################### Structures #######################
%for title, data in (("Crystal structures",protein.pdbs), ("Swissmodel", protein.swissmodel), ("Homologue structures", protein.pdb_matches)):
    %if data:
    ft.addFeature({
        data: ${str([{'x': structure.x, 'y': structure.y, 'id': structure.id, 'description': structure.description} for structure in data])|n},
        name: "${title}",
        className: "pdb",
        color: "lime",
        type: "rect",
        filter: "Domain"
    });
    %endif
%endfor