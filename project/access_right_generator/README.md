Module To Access Right Generator
===================================
How to use:
===========
1. **Create data in file security_set_up.py in each project**:
    * [1,1,1,1]: present 4 permissions: "perm_read", "perm_write", "perm_create", "perm_unlink"
    * **Example**:
        * g_hr_employee = "Employee"
        * g_user = "User"
        * g_manuf_user = "Manufacturing / Manager"
        * g_all = '' (all groups)
        * MODEL_ACCESS_RIGHTS = {
            ('nationality','accident.type.category', 'accident.type.rate',
            'activity.naf','admin.activity.type', 'admin.skill.activity',
            'admin.skill', 'autonomy.level'): {
            (g_hr_employee,g_user) : [0,1,1,1],
            (g_all):[1,1,1,1]
            }
            }
        * or MODEL_ACCESS_RIGHTS = {
            'mrp.bom': { g_hr_employee: [1,1,0,1]
            },
            'hr.employee': {
            g_hr_employee : [1,1,0,1],
            g_manuf_user: [1,0,0,1],
            g_all: [1,1,1,1]
            }
            }
2. **Update context**:
    * context.update({'module_name': 'your_module_name'})
3. **Call Function**
    * self.env['access.right.generator'].with_context(module_name='test_module').create_model_access_rights(MODEL_ACCESS_RIGHTS)
