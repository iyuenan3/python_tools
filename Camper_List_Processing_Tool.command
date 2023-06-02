#!/usr/bin/env python3
import os, sys, shutil, requests
import xlrd, xlwt
import time, datetime

path = os.path.dirname(sys.argv[0])
os.chdir(path)

def download_excel(workbook_name):
    cookies = {}
    headers = {}
    data    = {}
    url     = ''
    if os.path.exists(workbook_name):
        print('========== 《%s》 已存在，程序运行失败' % workbook_name)
        os._exit()
    else:
        print('========== 正在下载最新的营员列表《%s》，请稍等...' % workbook_name)
        response = requests.post(f'{url}', cookies=cookies, headers=headers, data=data)
        with open(workbook_name,"wb") as file:
            file.write(response.content)

def backup_oldfile(filename, folder):
    creation_time = time.strftime('_%Y_%m_%d-%H-%M-%S', time.localtime(os.path.getctime(filename)))
    new_filename = '%s%s.xls' % (filename.split('.')[0], creation_time)
    if not os.path.exists(folder):
        print('========== “%s”文件夹不存在，创建目录' % folder)
        os.makedirs(folder)
    print('========== 备份《%s》到“%s”文件夹下' % (filename, folder))
    shutil.move(filename, os.path.join(folder, new_filename))

def calculate_age(birth):
    try:
        time.strptime(birth, "%Y-%m-%d")
    except Exception:
        #raise Exception("时间参数错误 near : {}".format(birth))
        age = '待核实'
        return age
    birth_d = datetime.datetime.strptime(birth, "%Y-%m-%d")
    today_d = datetime.datetime.now()
    birth_t = birth_d.replace(year=today_d.year)
    if today_d > birth_t:
        age = today_d.year - birth_d.year
    else:
        age = today_d.year - birth_d.year - 1
    return age

def categorized_statistics(list, gender, city, assemblypoint):
    if gender == '男':
        list[0][1] +=1
    elif gender == '女':
        list[0][2] +=1
    if city == '北京市':
        list[0][5] +=1
    elif city == '上海市':
        list[0][6] +=1
    # 北京带队
    if '北京带队' in assemblypoint:
        list[0][7] +=1
    elif '北京飞机带队' in assemblypoint:
        list[0][7] +=1
    # 杭州东站
    elif '杭州东站' in assemblypoint:
        list[0][8] +=1
    # 上海虹桥
    elif '虹桥' in assemblypoint:
        list[0][9] +=1
    elif '上海高铁' in assemblypoint:
        list[0][9] +=1
    # 千岛湖高铁站
    elif '千岛湖高铁站' in assemblypoint:
        list[0][10] +=1
    # 萧山机场
    elif '萧山机场' in assemblypoint:
        list[0][11] +=1
    # 营地集合
    elif '营地集合' in assemblypoint:
        list[0][12] +=1
    # 其他
    else:
        list[0][13] +=1
    return list

def process_each_sheet(sheet, list):
    header_row = [0]*25
    for i in range(1,sheet.ncols):
        if '营员姓名' == sheet.cell(0,i).value.strip():
            header_row[0] = i
        elif '性别' == sheet.cell(0,i).value.strip():
            header_row[1] = i
        elif '出生日期' == sheet.cell(0,i).value.strip():
            header_row[2] = i
        elif '证件号' == sheet.cell(0,i).value.strip():
            header_row[4] = i
        elif '证件类型' == sheet.cell(0,i).value.strip():
            header_row[5] = i
        elif '对于冬夏令营我' in sheet.cell(0,i).value.strip():
            header_row[6] = i
        elif '营员英文名' == sheet.cell(0,i).value.strip():
            header_row[7] = i
        elif '身高' == sheet.cell(0,i).value.strip():
            header_row[8] = i
        elif '体重' == sheet.cell(0,i).value.strip():
            header_row[9] = i
        elif '所在城市' == sheet.cell(0,i).value.strip():
            header_row[10] = i
        elif '监护人联系电话' == sheet.cell(0,i).value.strip():
            header_row[11] = i
        elif '紧急联系人电话' == sheet.cell(0,i).value.strip() or '紧急联络人手机' == sheet.cell(0,i).value.strip():
            header_row[12] = i
        elif '饮食禁忌' == sheet.cell(0,i).value.strip() or '不吃的东西' in sheet.cell(0,i).value.strip():
            header_row[13] = i
        elif '过敏须知' == sheet.cell(0,i).value.strip() or '过敏源' in sheet.cell(0,i).value.strip():
            header_row[14] = i
        elif '过往病史' == sheet.cell(0,i).value.strip():
            header_row[15] = i
        elif '营员同屋备注' == sheet.cell(0,i).value.strip():
            header_row[16] = i
        elif '集合接驳点' == sheet.cell(0,i).value.strip():
            header_row[17] = i
        elif '去程航班信息' == sheet.cell(0,i).value.strip():
            header_row[18] = i
        elif '返程接驳点' == sheet.cell(0,i).value.strip():
            header_row[19] = i
        elif '返程航班信息' == sheet.cell(0,i).value.strip():
            header_row[20] = i
        # 如果表格中只有“航班信息”，则根据前一列是“集合接驳点”还是“返程接驳点”来判断是“去程航班”还是“返程航班”
        elif '航班信息' == sheet.cell(0,i).value.strip():
            if '集合接驳点' == sheet.cell(0,i-1).value.strip():
                header_row[18] = i
            elif '返程接驳点' == sheet.cell(0,i-1).value.strip():
                header_row[20] = i
        elif '备注' == sheet.cell(0,i).value.strip():
            header_row[21] = i
        elif '所属员工' == sheet.cell(0,i).value.strip():
            header_row[22] = i
        elif '营期' == sheet.cell(0,i).value.strip():
            header_row[23] = i
        elif '营种规格' == sheet.cell(0,i).value.strip():
            header_row[24] = i

    for row in range(1,sheet.nrows):
        member_info = [0]*25
        for col in range(0,len(member_info)):
            if header_row[col] == 0:
                member_info[col] = '待核实'
            else:
                member_info[col] = sheet.cell(row,header_row[col]).value.strip()
        if '未填写出行人' == sheet.cell(row,1):
            member_info[0] = '未填写出行人'
            member_info[1] = '订单营员数：'
            member_info[2] = int(sheet.cell(row,2).value)
        # Age = calculate_age(Birthday)
        member_info[3] = calculate_age(member_info[2])
        # 所在城市有‘,’分隔符，取分割后第二项（城市）
        if ',' in member_info[10]:
            member_info[10] = member_info[10].split(',')[1]

        #list.append([Name,Gender,Birthday,Age,Cert,CertType,Style,EngName,Rist,Weight,City,GuardianPhone,EmergencyPhone,DietTaboos,Allergy,PastMedical,RoommateNotes,AssemblyPoint,OutboundFlightInfor,ReturnPoint,ReturnFlightInfor,Notes,Employees,CampPeriod])
        list.append([
            member_info[0], member_info[1], member_info[2], member_info[3], member_info[4],
            member_info[5], member_info[6], member_info[7], member_info[8], member_info[9],
            member_info[10], member_info[11], member_info[12], member_info[13], member_info[14],
            member_info[15], member_info[16], member_info[17], member_info[18], member_info[19],
            member_info[20], member_info[21], member_info[22], member_info[23], member_info[24]
        ])
        list[0][0] +=1
        # 统计 性别、所在城市、集合接驳点 信息
        list = categorized_statistics(list, member_info[1], member_info[10], member_info[17])

    return list

def all_personnel_statistics(wb):
    # 创建二维列表用于存放总人数
    # 二维列表第一项为人数统计：
    #     总人数，男生人数，女生人数，男生占比，女生占比
    #     北京人数，上海人数
    #     北京带队，杭州东站，上海虹桥，千岛湖高铁站，萧山机场，营地集合，其他
    # 二维列表第二项开始为所有营员信息
    list = [[0,0,0,0,0,0,0,0,0,0,0,0,0,0]]

    sheetlist = wb.sheet_names()
    for i in sheetlist:
        list = process_each_sheet(wb[i], list)

    if float(list[0][0]) == 0:
        list[0][3] = '0.0%'
        list[0][4] = '0.0%'
    else:
        list[0][3] = '{:.1%}'.format(float(list[0][1]) / float(list[0][0]))
        list[0][4] = '{:.1%}'.format(float(list[0][2]) / float(list[0][0]))
    return list

def each_period_statistics(member_list, phase):
    # 创建二维列表用于存放每一期的人数
    # 二维列表第一项为人数统计：
    #     总人数，男生人数，女生人数，男生占比，女生占比
    #     北京人数，上海人数
    #     北京带队，杭州东站，上海虹桥，千岛湖高铁站，萧山机场，营地集合，其他
    # 二维列表第二项开始为当期营员信息
    phase_list = [[0,0,0,0,0,0,0,0,0,0,0,0,0,0]]
    for i in range(1,len(member_list)):
        if member_list[i][23] == phase:
            phase_list.append(member_list[i])
            phase_list[0][0] +=1
            phase_list = categorized_statistics(phase_list, member_list[i][1], member_list[i][10], member_list[i][17])

    if float(phase_list[0][0]) == 0:
        phase_list[0][3] = '0.0%'
        phase_list[0][4] = '0.0%'
    else:
        phase_list[0][3] = '{:.1%}'.format(float(phase_list[0][1]) / float(phase_list[0][0]))
        phase_list[0][4] = '{:.1%}'.format(float(phase_list[0][2]) / float(phase_list[0][0]))
    return phase_list

def write_member_to_form(sheet, list):
    # 创建表头
    sheet.write(0,0,'营员姓名')
    sheet.write(0,1,'性别')
    sheet.write(0,2,'出生日期')
    sheet.write(0,3,'年龄')
    sheet.write(0,4,'证件号')
    sheet.write(0,5,'证件类型')
    sheet.write(0,6,'对于冬夏令营我（家长）可能是那种情况')
    sheet.write(0,7,'营员英文名')
    sheet.write(0,8,'身高')
    sheet.write(0,9,'体重')
    sheet.write(0,10,'所在城市')
    sheet.write(0,11,'监护人联系电话')
    sheet.write(0,12,'紧急联系人电话')
    sheet.write(0,13,'饮食禁忌')
    sheet.write(0,14,'过敏须知')
    sheet.write(0,15,'过往病史')
    sheet.write(0,16,'营员同屋备注')
    sheet.write(0,17,'集合接驳点')
    sheet.write(0,18,'来程航班信息')
    sheet.write(0,19,'返程接驳点')
    sheet.write(0,20,'返程航班信息')
    sheet.write(0,21,'备注')
    sheet.write(0,22,'所属员工')
    sheet.write(0,23,'营期')
    sheet.write(0,24,'营种规格')

    for i in range(1,len(list)):
        for j in range(len(list[i])):
            sheet.write(i,j,list[i][j])

def write_summary_to_form(sheet, list, phase_name, index):
    sheet.write(0,index,phase_name)
    sheet.write(1,index,list[0][0])
    sheet.write(2,index,list[0][1])
    sheet.write(3,index,list[0][2])
    sheet.write(4,index,list[0][3])
    sheet.write(5,index,list[0][4])
    sheet.write(7,index,list[0][5])
    sheet.write(8,index,list[0][6])
    sheet.write(10,index,list[0][7])
    sheet.write(11,index,list[0][8])
    sheet.write(12,index,list[0][9])
    sheet.write(13,index,list[0][10])
    sheet.write(14,index,list[0][11])
    sheet.write(15,index,list[0][12])
    sheet.write(16,index,list[0][13])

############################################################ 主函数
Member_Workbook_Name = '营员列表.xls'
New_Workbook_Name = '小乔专属工具生成的新营员列表.xls'
Backup_Folder = '营员列表备份'
if os.path.exists(Member_Workbook_Name):
    backup_oldfile(Member_Workbook_Name, Backup_Folder)
if os.path.exists(New_Workbook_Name):
    backup_oldfile(New_Workbook_Name, Backup_Folder)

download_excel(Member_Workbook_Name)
Member_List = all_personnel_statistics(xlrd.open_workbook(Member_Workbook_Name))
Phase1_Name = '2022/07/03-2022/07/09'
Phase2_Name = '2022/07/10-2022/07/16'
Phase3_Name = '2022/07/17-2022/07/23'
Phase4_Name = '2022/07/24-2022/07/30'
Phase5_Name = '2022/07/31-2022/08/06'
Phase6_Name = '2022/08/07-2022/08/13'
Phase7_Name = '2022/08/14-2022/08/20'
Phase8_Name = '2022/08/21-2022/08/27'
Phase1_List = each_period_statistics(Member_List, Phase1_Name)
Phase2_List = each_period_statistics(Member_List, Phase2_Name)
Phase3_List = each_period_statistics(Member_List, Phase3_Name)
Phase4_List = each_period_statistics(Member_List, Phase4_Name)
Phase5_List = each_period_statistics(Member_List, Phase5_Name)
Phase6_List = each_period_statistics(Member_List, Phase6_Name)
Phase7_List = each_period_statistics(Member_List, Phase7_Name)
Phase8_List = each_period_statistics(Member_List, Phase8_Name)

# 创建新工作表
NEW_WORKBOOK = xlwt.Workbook()
Summary_Info = NEW_WORKBOOK.add_sheet('营员汇总信息',cell_overwrite_ok=True)
Member_Sheet = NEW_WORKBOOK.add_sheet('营员总列表',cell_overwrite_ok=True)
Phase1_Sheet = NEW_WORKBOOK.add_sheet(Phase1_Name.replace('/',''),cell_overwrite_ok=True)
Phase2_Sheet = NEW_WORKBOOK.add_sheet(Phase2_Name.replace('/',''),cell_overwrite_ok=True)
Phase3_Sheet = NEW_WORKBOOK.add_sheet(Phase3_Name.replace('/',''),cell_overwrite_ok=True)
Phase4_Sheet = NEW_WORKBOOK.add_sheet(Phase4_Name.replace('/',''),cell_overwrite_ok=True)
Phase5_Sheet = NEW_WORKBOOK.add_sheet(Phase5_Name.replace('/',''),cell_overwrite_ok=True)
Phase6_Sheet = NEW_WORKBOOK.add_sheet(Phase6_Name.replace('/',''),cell_overwrite_ok=True)
Phase7_Sheet = NEW_WORKBOOK.add_sheet(Phase7_Name.replace('/',''),cell_overwrite_ok=True)
Phase8_Sheet = NEW_WORKBOOK.add_sheet(Phase8_Name.replace('/',''),cell_overwrite_ok=True)

write_member_to_form(Phase1_Sheet,Phase1_List)
write_member_to_form(Phase2_Sheet,Phase2_List)
write_member_to_form(Phase3_Sheet,Phase3_List)
write_member_to_form(Phase4_Sheet,Phase4_List)
write_member_to_form(Phase5_Sheet,Phase5_List)
write_member_to_form(Phase6_Sheet,Phase6_List)
write_member_to_form(Phase7_Sheet,Phase7_List)
write_member_to_form(Phase8_Sheet,Phase8_List)
write_member_to_form(Member_Sheet,Member_List)

# 创建表头
Summary_Info.write(1,0,'总营员')
Summary_Info.write(2,0,'男营员')
Summary_Info.write(3,0,'女营员')
Summary_Info.write(4,0,'男营员占比')
Summary_Info.write(5,0,'女营员占比')
Summary_Info.write(7,0,'北京市人数')
Summary_Info.write(8,0,'上海市人数')
Summary_Info.write(10,0,'北京带队')
Summary_Info.write(11,0,'杭州东站')
Summary_Info.write(12,0,'上海虹桥')
Summary_Info.write(13,0,'千岛湖高铁站')
Summary_Info.write(14,0,'萧山机场')
Summary_Info.write(15,0,'营地集合')
Summary_Info.write(16,0,'其他')
write_summary_to_form(Summary_Info, Member_List, '所有营期', 1)
write_summary_to_form(Summary_Info, Phase1_List, Phase1_Name, 2)
write_summary_to_form(Summary_Info, Phase2_List, Phase2_Name, 3)
write_summary_to_form(Summary_Info, Phase3_List, Phase3_Name, 4)
write_summary_to_form(Summary_Info, Phase4_List, Phase4_Name, 5)
write_summary_to_form(Summary_Info, Phase5_List, Phase5_Name, 6)
write_summary_to_form(Summary_Info, Phase6_List, Phase6_Name, 7)
write_summary_to_form(Summary_Info, Phase7_List, Phase7_Name, 8)
write_summary_to_form(Summary_Info, Phase8_List, Phase8_Name, 9)

if os.path.exists(New_Workbook_Name):
    print('========== 《%s》已存在，程序运行失败' % New_Workbook_Name)
    os._exit()
else:
    print('========== 正在生成最新的《%s》' % New_Workbook_Name)
    NEW_WORKBOOK.save(New_Workbook_Name)
    print('========== 最新的《%s》生成成功' % New_Workbook_Name)
