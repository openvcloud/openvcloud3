[actor] @dbtype:mem,fs
    """
    image manager
    """
    method:create
        """
        create image
        """
        var:name str,,name of the image @index
        var:description str,,extra description of the image @optional
        var:size int,, minimal disk size in Gigabyte @optional
        var:accountId str,,id of account to which this image belongs @optional
        var:type str,, type of image @optional
        var:username str,, default username for image image @optional
        var:password str,, default password for image @optional
        var:referenceId str,,Path of image on storage server
        result:int

    method:delete
        """
        delete image
        """
        var:imageId str,,id of image to be deleted
        result:bool

    method:enable
        """
        enable image
        """
        var:imageId str,,id of image to be enabled
        result:bool

    method:edit
        """
        edit image
        """
        var:imageId str,,id of image to be enabled
        var:name str,,new name of image @optional
        var:type str,,new type of image @optional
        var:description str,,new description of image @optional
        var:username str,,new username of image @optional
        var:password str,,new password of image @optional
        result:bool

    method:disable
        """
        disable image
        """
        var:imageId str,,id of image to be disabled
        result:bool


    method:updateNodes
        """
        Update which nodes have this image available
        """
        var:imageId str,,id of image
        var:enabledStacks list,,list of enabled stacks @optional
        result:bool
