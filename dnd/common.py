def format_errors(errors):
    return "\n".join(["""
<div class="alert alert-danger alert-dismissable fade in">
    <a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>
    {}
</div>
""".format(message) for message in errors])
