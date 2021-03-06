#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# Copyright (C) 2014  Jamie Duncan (jamie.e.duncan@gmail.com)

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# File Name : test.py
# Creation Date : 07-02-2014
# Created By : Jamie Duncan
# Last Modified : Sat 13 Sep 2014 10:55:29 PM EDT
# Purpose : SOSCleaner unittests
import sys
sys.path.append('soscleaner/')
import unittest
from soscleaner import SOSCleaner
import os
import shutil
from ipaddr import IPv4Network, IPv4Address, IPv6Network, IPv6Address

class SOSCleanerTests(unittest.TestCase):
    def _setUpHostname(self, t='fqdn', remove=False):
        hostname_f = os.path.join(self.testdir, 'hostname')
        if remove:
            os.remove(hostname_f)
            return True
        fh = open(hostname_f, 'w')
        if t == 'non-fqdn':
            fh.write('myhost\n')
        else:
            fh.write('myhost.myserver.com\n')
        fh.close()

    def _setUpHostnamePath(self, t='fqdn', remove=False):
        hostname_f = os.path.join(self.testdir, 'hostname2')
        if remove:
            os.remove(hostname_f)
            return True
        fh = open(hostname_f, 'w')
        if t == 'non-fqdn':
            fh.write('myhost2\n')
        else:
            fh.write('myhost2.myserver2.com\n')
        fh.close()

    def setUp(self):
        self.testdir = 'testdata/sosreport_dir'
        self.cleaner = SOSCleaner(quiet=True)
        self.cleaner.origin_path, self.cleaner.dir_path, self.cleaner.session, self.cleaner.logfile, self.cleaner.uuid = self.cleaner._prep_environment()
        self.cleaner._start_logging(self.cleaner.logfile)
        self._setUpHostname()

    def _artifact_cleanup(self,directory):
        #clean up the /tmp directory between tests, when artifacts are created
        for f in os.listdir(directory):
            a = os.path.join(directory,f)
            if 'soscleaner' in f:
                if os.path.isdir(a):
                    shutil.rmtree(a)
                else:
                    os.remove(a)

    def tearDown(self):
        self._artifact_cleanup('/tmp')

    def test0_prep_environment(self):
        # _prep_environment() should create 4 values
        # * self.origin_path - path the sosreport is extracted to
        # * self.dir_path - path cleaned report is written to
        # * self.session - soscleaner-$timestamp - used for naming files/reports/etc.
        # * self.logfile - location of logfile

        self.assertTrue('soscleaner-origin' in self.cleaner.origin_path)
        self.assertTrue('soscleaner' in self.cleaner.dir_path)
        self.assertTrue('soscleaner' in self.cleaner.session)
        self.assertTrue('log' in self.cleaner.logfile)

    def test1_get_hostname_fqdn(self):
        # _get_hostname should return the hostname and domainname from the sosreport. testing with an fqdn
        self.cleaner.dir_path = 'testdata/sosreport_dir'
        self._setUpHostname(t='fqdn')
        host, domain = self.cleaner._get_hostname()
        self.assertTrue(host == 'myhost')
        self.assertTrue(domain == 'myserver.com')

    def test2_get_hostname_nonfqdn(self):
        # testing with a non-fqdn
        self.cleaner.dir_path = 'testdata/sosreport_dir'
        self._setUpHostname(t='non-fqdn')
        host, domain = self.cleaner._get_hostname()
        self.assertTrue(host == 'myhost')
        self.assertTrue(domain == None)

    def test3_get_hostname_nohostnamefile(self):
        # testing with no hostname file
        self.cleaner.dir_path = 'testdata/sosreport_dir'
        self._setUpHostname(remove=True)
        host,domain = self.cleaner._get_hostname()
        self.assertTrue(host == None)
        self.assertTrue(domain == None)

    def test4_get_hostname_path_fqdn(self):
        # _get_hostname should return the hostname and domainname from the sosreport. testing with an fqdn
        self.cleaner.dir_path = 'testdata/sosreport_dir'
        self._setUpHostnamePath(t='fqdn')
        host, domain = self.cleaner._get_hostname('hostname2')
        self.assertTrue(host == 'myhost2')
        self.assertTrue(domain == 'myserver2.com')

    def test5_get_hostname_path_nonfqdn(self):
        # testing with a non-fqdn
        self.cleaner.dir_path = 'testdata/sosreport_dir'
        self._setUpHostnamePath(t='non-fqdn')
        host, domain = self.cleaner._get_hostname('hostname2')
        self.assertTrue(host == 'myhost2')
        self.assertTrue(domain == None)

    def test6_get_hostname_path_nohostnamefile(self):
        # testing with no hostname file
        self.cleaner.dir_path = 'testdata/sosreport_dir'
        self._setUpHostnamePath(remove=True)
        host,domain = self.cleaner._get_hostname('hostname2')
        self.assertTrue(host == None)
        self.assertTrue(domain == None)

    def test7_obfuscate_hosts_file(self):
        # testing hosts file extra processing
        self.cleaner.dir_path = 'testdata/sosreport_dir'
        self.cleaner._process_hosts_file()
        self.assertTrue('myhost' in self.cleaner.hn_db.values())

    def test8_skip_files(self):
        d = 'testdata/sosreport_dir'
        files = ['test.bin','test.txt']
        skip_list = self.cleaner._skip_file(d,files)
        self.assertTrue('test.bin' in skip_list)
        self.assertTrue('test.txt' not in skip_list)

    def test9_extract_sosreport_dir(self):
        d = self.cleaner._extract_sosreport(self.testdir)
        self.assertTrue(d == self.testdir)

    def test10_extract_sosreport_gz(self):
        d = self.cleaner._extract_sosreport('testdata/sosreport1.tar.gz')
        check_d = '/tmp/soscleaner-origin-%s/sosreport_dir' % self.cleaner.uuid
        self.assertTrue(d == check_d)

    def test11_extract_sosreport_bz(self):
        d = self.cleaner._extract_sosreport('testdata/sosreport1.tar.gz')
        check_d = '/tmp/soscleaner-origin-%s/sosreport_dir' % self.cleaner.uuid
        self.assertTrue(d == check_d)

    def test12_extract_sosreport_xz(self):
        d = self.cleaner._extract_sosreport('testdata/sosreport1.tar.xz')
        check_d = '/tmp/soscleaner-origin-%s/sosreport_dir' % self.cleaner.uuid
        self.assertTrue(d == check_d)

    def test13_clean_line(self):
        hostname = 'myhost.myservers.com'
        ip = '192.168.1.10'
        line = "foo bar %s some words %s more words" % (hostname, ip)
        self.cleaner.hostname = hostname
        self.cleaner.process_hostnames = True
        self.cleaner.domainname = 'example.com'
        self.cleaner.dn_db['example.com'] = 'myservers.com'
        new_line = 'foo bar %s some words %s more words' % (self.cleaner._hn2db(hostname), self.cleaner._ip4_2_db(ip))
        self.assertTrue(self.cleaner._clean_line(line) == new_line)

    def test14_make_dest_env(self):
        self.cleaner.report = self.testdir
        self.cleaner._make_dest_env()
        self.assertTrue(os.path.isdir(self.cleaner.dir_path))

    def test15_create_archive(self):
        origin_test = '/tmp/origin-testdir'
        dir_test = '/tmp/path-testdir'
        for d in origin_test, dir_test:
            if not os.path.exists(d):
                shutil.copytree(self.testdir, d)
        self.cleaner.origin_path = origin_test
        self.cleaner.dir_path = dir_test
        self.cleaner._create_archive()
        self.assertTrue(os.path.isfile(self.cleaner.archive_path))
        self.assertFalse(os.path.exists(origin_test))
        self.assertFalse(os.path.exists(dir_test))

    def test16_domains2db_fqdn(self):
        self.cleaner.domainname = 'myserver.com'
        self.cleaner.domains = ['foo.com','bar.com']
        self.cleaner._domains2db()
        self.assertTrue(self.cleaner.domainname in self.cleaner.dn_db.values())
        self.assertTrue('foo.com' in self.cleaner.dn_db.values())
        self.assertTrue('bar.com' in self.cleaner.dn_db.values())

    def test17_file_list(self):
        x = self.cleaner._file_list('testdata/sosreport_dir')
        self.assertTrue('testdata/sosreport_dir/var/log/messages' in x)
        self.assertTrue('testdata/sosreport_dir/hostname' in x)

    def test18_create_hn_report(self):
        test_hn = 'myhost.myserver.com'
        self.cleaner.domainname = 'myserver.com'
        self.cleaner.process_hostnames = True
        test_o_hn = self.cleaner._hn2db(test_hn)
        self.cleaner._create_hn_report()
        fh = open(self.cleaner.hn_report,'r')
        x = fh.readlines()
        self.assertTrue(test_hn in x[1])
        self.assertTrue(test_o_hn in x[1])

    def test19_create_hn_report_nohn(self):
        self.cleaner.process_hostnames = False
        self.cleaner._create_hn_report()
        fh = open(self.cleaner.hn_report, 'r')
        lines = fh.readlines()
        self.assertTrue(lines[1] == 'None,None\n')

    def test20_create_dn_report(self):
        self.cleaner.domainname = 'myserver.com'
        self.cleaner.domains = ['myserver.com']
        self.cleaner._domains2db()
        self.cleaner._create_dn_report()
        fh = open(self.cleaner.dn_report,'r')
        x = fh.readlines()
        self.assertTrue( self.cleaner.domainname in x[1])

    def test21_create_dn_report_none(self):
        self.cleaner._create_dn_report()
        fh = open(self.cleaner.dn_report,'r')
        x = fh.readlines()
        self.assertTrue( x[1] == 'None,None\n')

    def test22_clean_file(self):
        test_file = '/tmp/clean_file_test'
        shutil.copyfile('testdata/sosreport_dir/var/log/messages', test_file)
        self.cleaner.process_hostnames = True
        self.cleaner.domains = ['myserver.com','foo.com']
        self.cleaner.domainname = 'myserver.com'
        self.cleaner.hostname = 'myhost'
        self.cleaner._domains2db()
        self.cleaner._clean_file(test_file)
        fh = open(test_file,'r')
        data = ', '.join(fh.readlines())
        fh.close()
        self.assertTrue(self.cleaner._hn2db(self.cleaner.hostname) in data)
        self.assertTrue(self.cleaner._hn2db('foohost.foo.com') in data)
        os.remove(test_file)    #clean up

    def test23_sub_hostname_hyphens(self):
        self.cleaner.domains=['myserver.com']
        self.cleaner.domainname='myserver.com'
        self.cleaner.hostname='myhost'
        self.cleaner._domains2db()
        line = 'this is myhost.myserver.com and this is my-host.myserver.com'
        new_line = self.cleaner._sub_hostname(line)
        self.assertTrue('my' not in new_line)

    def test24_extra_files(self):
        files = ['testdata/extrafile1','testdata/extrafile2','testdata/extrafile3']
        self.cleaner._clean_files_only(files)
        self.assertTrue(os.path.isdir(self.cleaner.dir_path))
        self.assertTrue(os.path.exists(os.path.join(self.cleaner.dir_path, 'extrafile3')))

    def test25_create_archive_nososreport(self):
        files = ['testdata/extrafile1','testdata/extrafile2','testdata/extrafile3']
        self.cleaner._clean_files_only(files)
        self.assertTrue(os.path.exists(os.path.join(self.cleaner.dir_path, 'extrafile3')))

    def test26_extra_files_nonexistent(self):
        files = ['testdata/extrafile1','testdata/extrafile2','testdata/extrafile3', 'testdata/bogusfile']
        self.cleaner._clean_files_only(files)
        self.assertTrue(os.path.exists(os.path.join(self.cleaner.dir_path, 'extrafile3')))
        self.assertFalse(os.path.exists(os.path.join(self.cleaner.dir_path, 'bogusfile')))

    def test27_clean_files_only_originexists(self):
        os.makedirs(self.cleaner.origin_path)
        files = ['testdata/extrafile1','testdata/extrafile2','testdata/extrafile3', 'testdata/bogusfile']
        self.cleaner._clean_files_only(files)
        self.assertTrue(os.path.exists(self.cleaner.origin_path))

    def test28_add_keywords_badfile(self):
        self.cleaner.keywords = ['testdata/keyword_bad.txt']
        self.cleaner._keywords2db()
        self.assertTrue(self.cleaner.kw_count == 0)

    def test29_add_keywords(self):
        self.cleaner.keywords = ['testdata/keyword1.txt','testdata/keyword2.txt']
        self.cleaner._keywords2db()
        self.assertTrue(self.cleaner.kw_count == 8)
        self.assertTrue(all(['foo' in self.cleaner.kw_db.keys(),'some' in self.cleaner.kw_db.keys()]))

    def test30_sub_keywords(self):
        self.cleaner.keywords = ['testdata/keyword1.txt']
        self.cleaner._keywords2db()
        test_line = 'this is a sample foo bar. this should be different bar foo.'
        new_line = self.cleaner._sub_keywords(test_line)
        self.assertTrue(all(['keyword0' in new_line, 'keyword1' in new_line]))

    def test31_create_ip_report(self):
        self.cleaner._ip4_2_db('192.168.122.100')
        self.cleaner._create_ip_report()
        fh = open(self.cleaner.ip_report,'r')
        x = fh.readlines()
        self.assertTrue( '192.168.122.100' in x[1])

    def test32_sub_hostname_front_of_line(self):
        self.cleaner.domains=['myserver.com']
        self.cleaner.domainname='myserver.com'
        self.cleaner.hostname='myhost'
        self.cleaner._domains2db()
        line = 'myhost.myserver.com and this is my-host.myserver.com'
        new_line = self.cleaner._sub_hostname(line)
        self.assertTrue('my' not in new_line)

    def test33_routes_file(self):
        self.cleaner.dir_path = 'testdata/sosreport_dir'
        self.cleaner._process_route_file()
        self.assertTrue(self.cleaner.net_db[0][0].compressed == '10.0.0.0/8')

    def test34_routes_file_absent(self):
        self.cleaner.dir_path = 'testdata/'
        self.cleaner._process_route_file()

    def test35_existing_network(self):
        self.cleaner.dir_path = 'testdata/sosreport_dir'
        data = self.cleaner._ip4_add_network('10.0.0.0/8')
        self.assertTrue(self.cleaner._ip4_network_in_db(IPv4Network('10.0.0.0/8')) == True)

    def test36_add_loopback(self):
        self.cleaner._add_loopback_network()
        self.assertTrue(self.cleaner.net_metadata['127.0.0.0']['host_count'] == 0)
        self.assertTrue(self.cleaner._ip4_network_in_db(IPv4Network('127.0.0.0/8')) == True)

    def test37_dup_networks(self):
        self.cleaner._ip4_add_network('10.0.0.0/8')
        self.cleaner._ip4_add_network('10.0.0.0/8')
        self.assertTrue(self.cleaner._ip4_network_in_db(IPv4Network('10.0.0.0/8')) == True)

    def test38_find_existing_network(self):
        self.cleaner._ip4_add_network('10.0.0.0/8')
        data = self.cleaner._ip4_find_network('10.0.0.1')
        self.assertTrue(data == IPv4Address('129.0.0.0'))
