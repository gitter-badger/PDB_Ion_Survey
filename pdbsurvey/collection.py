def _emit(key, value, content_handler, attr_prefix='@', cdata_key='#text',
          depth=0, preprocessor=None, pretty=False, newl='\n', indent='\t',
          full_document=True):
    '''I do not know what this does.
    -------------------------
    Credit to: Martin Blech
    '''
    if preprocessor is not None:
        result = preprocessor(key, value)
        if result is None:
            return
        key, value = result
    if (not hasattr(value, '__iter__')
            or isinstance(value, _basestring)
            or isinstance(value, dict)):
        value = [value]
    for index, v in enumerate(value):
        if full_document and depth == 0 and index > 0:
            raise ValueError('document with multiple roots')
        if v is None:
            v = OrderedDict()
        elif not isinstance(v, dict):
            v = _unicode(v)
        if isinstance(v, _basestring):
            v = OrderedDict(((cdata_key, v),))
        cdata = None
        attrs = OrderedDict()
        children = []
        for ik, iv in v.items():
            if ik == cdata_key:
                cdata = iv
                continue
            if ik.startswith(attr_prefix):
                attrs[ik[len(attr_prefix):]] = iv
                continue
            children.append((ik, iv))
        if pretty:
            content_handler.ignorableWhitespace(depth * indent)
        content_handler.startElement(key, AttributesImpl(attrs))
        if pretty and children:
            content_handler.ignorableWhitespace(newl)
        for child_key, child_value in children:
            _emit(child_key, child_value, content_handler,
                  attr_prefix, cdata_key, depth+1, preprocessor,
                  pretty, newl, indent)
        if cdata is not None:
            content_handler.characters(cdata)
        if pretty and children:
            content_handler.ignorableWhitespace(depth * indent)
        content_handler.endElement(key)
        if pretty and depth:
            content_handler.ignorableWhitespace(newl)

def unparse(input_dict, output=None, encoding='utf-8', full_document=True,
            **kwargs):
    """Emit an XML document for the given `input_dict`.
    The resulting XML document is returned as a string, but if `output` (a
    file-like object) is specified, it is written there instead.
    Dictionary keys prefixed with `attr_prefix` (default=`'@'`) are interpreted
    as XML node attributes, whereas keys equal to `cdata_key`
    (default=`'#text'`) are treated as character data.
    The `pretty` parameter (default=`False`) enables pretty-printing. In this
    mode, lines are terminated with `'\n'` and indented with `'\t'`, but this
    can be customized with the `newl` and `indent` parameters.
    -------------------------
    Credit to: Martin Blech
    """
    if full_document and len(input_dict)!=1:
        raise ValueError('Document must have exactly one root.')
    must_return=False
    if output is None:
        output=StringIO()
        must_return=True
    content_handler=XMLGenerator(output, encoding)
    if full_document:
        content_handler.startDocument()
    for key, value in input_dict.items():
        _emit(key, value, content_handler, full_document=full_document,
              **kwargs)
    if full_document:
        content_handler.endDocument()
    if must_return:
        value=output.getvalue()
        try:  # pragma no cover
            value=value.decode(encoding)
        except AttributeError:  # pragma no cover
            pass
        return value

def get_proteins(ionname):
    """Searches PDB for files with a specified bound ion.
    
    :Arguments:
        *ionname*
            name of desired ion
    :Returns:
        *idlist*
            ids of all PDB files containing ions with name ionname
   -------------------------
    Credit to: William Gilpin
    """
    query_params=dict()
    querytype='ChemCompIdQuery'
    query_params['queryType']='org.pdb.query.simple.ChemCompIdQuery'
    query_params['description']='Chemical ID(s):  '+ionname+' and Polymeric type is Any'
    query_params['chemCompId']=ionname
    query_params['polymericType']='Any'
    scan_params=dict()
    scan_params['orgPdbQuery']=query_params
    url='http://www.rcsb.org/pdb/rest/search'
    queryText=unparse(scan_params, pretty=True)
    queryText=queryText.encode()
    req=urllib2.Request(url, data=queryText)
    f=urllib2.urlopen(req)
    result=f.read()
    idlist=str(result)
    idlist=idlist.split('\n')
    return idlist

def get_pdb_file(pdb_id, compression=False):
    '''Get the full PDB file associated with a PDB_ID
    :Arguments:
        *pdb_id*
            four character string giving a pdb entry of interest
        *compression
            retrieve a compressed (gz) version of the file if True
    :Returns:
        *pdb_id.pdb*
            pdb file corresponding to pdb_id
    -------------------------
    Credit to: William Gilpin
    '''
    fullurl='http://www.rcsb.org/pdb/download/downloadFile.do?fileFormat=pdb'
    if compression:
        fullurl += '&compression=YES'
    else:
        fullurl += '&compression=NO'
    fullurl += '&structureId=' + pdb_id
    req=urllib2.Request(fullurl)
    f=urllib2.urlopen(req)
    result=f.read()
    result=result.decode('unicode_escape')
    if not os.path.exists('/nfs/homes/kreidy/PDB\ API/'+pdb_id+'.pdb'):
        f_out=open(pdb_id+'.pdb', 'w')
        f_out.write(result)
        f_out.close()
