/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";

export class ListItadmin extends ListController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
    }

    async onClickImportarXML() {
        return this.action.doAction({
            name: "Attach Files",
            type: 'ir.actions.act_window',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            res_model: 'multi.file.attach.xmls.wizard'
        });
    }

    async onClickDescargaXDia() {
        return this.action.doAction({
            name: "Descarga x Dia",
            type: 'ir.actions.act_window',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            res_model: 'descarga.x.dia.wizard'
        });
    }

    async onImportFIELSatInvoice() {
        await this.orm.call('res.company', 'import_current_company_invoice', []);
        this.actionService.doAction('reload');
    }

    async onClickSincronizarDocumentos() {
        await this.orm.call('ir.attachment', 'update_status_from_ir_attachment_document', []);
        this.actionService.doAction('reload');
    }
}

export const itadmin = {
    ...listView,
    Controller: ListItadmin,
};

registry.category("views").add("itadmin_tree", itadmin);
