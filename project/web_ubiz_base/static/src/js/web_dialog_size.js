openerp.web_ubiz_base = function(instance){
    var _t = instance.web._t,
    _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.WebClient.include({

        start: function() {
            this.set('title_part', {"zopenerp": "Ubiz"});
            return this._super();
            },
        });
}