# cloudflare-zabbix

A Cloudflare-Zabbix integration to monitor and calculate the total amount of all status codes from  different sites in a
given range of time. Also returns the percentage of 5xx errors in the same range of time.


![git3](https://user-images.githubusercontent.com/44653624/68424507-ed7d2780-0182-11ea-9c05-b9a01c64f7f5.png)



![git2](https://user-images.githubusercontent.com/44653624/68424514-f3730880-0182-11ea-8272-53c2162ceb91.png)







# Instructions: 


 1) Execute the following command line:
    `sudo pip3 install -r requirements.txt`

 2) Modify the configuration file `cloudflare.ini`

 3) Locate the files `cloudflare.py` and `cloudflare.ini` inside
    `/usr/lib/zabbix/externalscripts` (depends on linux distribution ) and give ownership
    of those files to the user that runs the `zabbix_server` process



 4) Execute the following command line:
    `/usr/bin/python3 /usr/lib/zabbix/externalscripts/cloudflare.py --create`

   This command line will create a zabbix `hostgroup`  called `Cloudflare_Status_Codes`
   and will also create the hosts referenced in the configuration file 
   `cloudflare.ini` . It will assign a lld rule and a item prototype 
   to each one of those previously created hosts.
   
   ![Screenshot_2019-11-07 Search](https://user-images.githubusercontent.com/44653624/68424543-008ff780-0183-11ea-9d93-f713184df5ca.png)

   

   The item prototype will create one item per status code discovered through
   low lever discovery rule and also will create a item called `Porcentaje_errores_500`
   that will show the percentage of 5xx errors for each host
   
   ![git1](https://user-images.githubusercontent.com/44653624/68424523-f79f2600-0182-11ea-8559-18f5fd0a2fd3.png)

    
 5) Wait for 30 minutes and the items data will be populated.

# cloudflare.ini:

Configuration file for `cloudflare.py`

Write the data in the following format
```
cloudflare_user = user@example.com

cloudflare_token = 7evfset01f1324156378b24d922a287e908ph 
```

The Zabbix user must be a `Zabbix Super Admin` type of user








Author: Simon Malave <simongmalav@gmail.com>
