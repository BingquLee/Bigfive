������scws��libsvm

scws��

����python2��python3�ᱨ��
8����װscws
	�汾��SCWS-1.2.3

(1). ȡ�� scws-1.2.3 �Ĵ���
wget http://www.xunsearch.com/scws/down/scws-1.2.3.tar.bz2
	

(2). �⿪ѹ����
tar xvjf scws-1.2.3.tar.bz2
	

(3). ����Ŀ¼ִ�����ýű��ͱ���
cd scws-1.2.3
./configure --prefix=/usr/local/scws

make

make install


(4). �ֵ�����
cd /usr/local/scws/etc

��Ҫע������޸��ļ�Ȩ�ޣ�
wget?http://www.xunsearch.com/scws/down/scws-dict-chs-utf8.tar.bz2
		wget?http://www.xunsearch.com/scws/down/scws-dict-cht-utf8.tar.bz2
tar xvjf scws-dict-chs-utf8.tar.bz2

tar xvjf scws-dict-cht-utf8.tar.bz2

sudo chmod 664 dict_cht.utf8.xdb

sudo chmod 664 dict.utf8.xdb
	

(5). ��װpyscws��
git clone https://github.com/MOON-CLJ/pyscws.git
cd pyscws

python setup.py install
·�����ã���֤import scws����������gedit /etc/ld.so.conf�����һ��/usr/local/scws/lib/��Ȼ��sudo ldconfig


python3�汾��
����
https://github.com/xyanyue/python3_scws

��Ȼ���Ȱ�װscws��c�汾
Ȼ��ʹ��setup.pyֱ�Ӱ�װ��ע����Ҫ�Һ�python3��include�����ļ��в���scws.c��ͷ�ļ��иĺã�Ȼ���������������͵���
����İ�װ������΢�е�Ī�������֮��������Ƚ���ѧ�����Զ����ԣ�������򵥵Ļ������setup.py��


libsvm��
һ�����أ�
��ַ��http://www.csie.ntu.edu.tw/~cjlin/libsvm/oldfiles/
��ѡ��libsvm-3.22.tar.gz

������ѹ��
tar -zxvf libsvm-3.22.tar.gz

�������룺
���նˣ�
1. ����libsvm-3.22Ŀ¼�£�ִ��make��

2. ����libsvm-3.22/python
 ��Ŀ¼�£�ִ��make��
�ġ�ʹ��
��libsvm-3.22/python
����svmutil����