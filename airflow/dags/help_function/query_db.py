import pandas as pd
from airflow.providers.mysql.hooks.mysql import MySqlHook


def insert_db(df, conn, name_table):
    cursor = conn.cursor()
    for col in df.columns:
        df[col] = df[col].astype(str)
    lst_col = list(df.columns)
    lst_val = ['%s']*len(list(df.columns))
    str_col = ','.join(lst_col)
    str_val = ','.join(lst_val)

    # try:
    sql = f'''INSERT INTO {name_table} ({str_col}) VALUES ({str(str_val)})'''
    for index, row in df.iterrows():
        try:
            val = df.loc[index,:].values.tolist()
            if(type(val[0])==list):
                val = val[0]
            cursor.execute(sql, tuple(val))
            cursor.execute('COMMIT;')
            print('Insert successful')
        except Exception as e:
            print('Insert error: ',e)
    cursor.close()
        
    # except Exception as e:
    #     print('Insert error: ',e)
    #     cursor.close()


