# coding=utf-8

from . import upload, download

class Result:
	SUCCESS = 0
	FAILURE = 1
	SKIPPED = 2


def testCase(name, setUp=None, tearDown=None, requiredFlags=[], *args, **kwargs):
	def wrap(method):
		def call(automated=False, *args, **kwargs):
			import time, traceback
			print "=" * 50
			print "Test case: %s" % name
			print "-" * 50
			result = Result.FAILURE
			start = time.time()
			setUpResult = None
			try:
				if requiredFlags:
					flags = account_info()["flags"]
					for flag in requiredFlags:
						if not flag in flags:
							print "Skipping test because of missing flag: %s" % flag
							result = Result.SKIPPED
							return
				try:
					setUpResult = setUp(name, *args, **kwargs) if setUp else None
				except:
					print "-" * 50
					print "Setup failed"
					traceback.print_exc()
					result = Result.FAILURE
					return
				start = time.time()
				try:
					method(setUpResult, *args, **kwargs)
					result = Result.SUCCESS
				except:
					print "-" * 50
					traceback.print_exc()
					if not automated:
						raw_input("Press enter to continue")
				try:
					if tearDown:
						tearDown(setUpResult)
				except:
					print "-" * 50
					print "Teardown failed, some resources are still used"
					traceback.print_exc()
					result = Result.FAILURE
					return
			except:
				pass
			finally:
				print "-" * 50
				if result == Result.SUCCESS:
					print "Test succeeded", "duration: %.1f sec" % (time.time() - start)
				if result == Result.SKIPPED:
					print "Test skipped"
				if result == Result.FAILURE:
					print "TEST FAILED", "duration: %.1f sec" % (time.time() - start)
				print "=" * 50
				return result

		return call

	return wrap


def testSuite(tests, automated=False):
	import time
	failed = 0
	skipped = 0
	start = time.time()
	for test in tests:
		result = test(automated=automated)
		if result == Result.FAILURE:
			failed += 1
		if result == Result.SKIPPED:
			skipped += 1
		print
	print "*" * 50
	print "Tests complete, %d of %d tests failed (%d skipped), total duration: %.1f sec" % (
	failed, len(tests), skipped, time.time() - start)
	print "*" * 50


def createStarTopology(topId, nodeCount=3, nodeType="openvz", prepare=False, start=False):
	print "Creating star topology of %d nodes of type %s..." % (nodeCount, nodeType)
	switch = element_create(topId, "tinc_vpn")
	switch_ports = []
	nodes = []
	ifaces = []
	connections = []
	for _ in xrange(0, nodeCount):
		node = element_create(topId, nodeType)
		nodes.append(node)
		iface = element_create(topId, "%s_interface" % nodeType, node["id"])
		ifaces.append(iface)
		switch_port = element_create(topId, "tinc_endpoint", switch["id"])
		switch_ports.append(switch_port)
		con = connection_create(iface["id"], switch_port["id"])
		connections.append(con)
	if prepare:
		topology_action(topId, "prepare")
	if start:
		topology_action(topId, "start")
	return nodes, ifaces, switch, switch_ports, connections


def isSuperset(obj1, obj2, path=""):
	# checks whether obj1 is a superset of obj2
	if obj2 is None:
		return (True, None)
	if isinstance(obj1, dict):
		if not isinstance(obj2, dict):
			return (False, "Type mismatch: %s, is dict instead of %s" % (path, type(obj2)))
		for key in obj2:
			if not key in obj1:
				return (False, "Key %s missing: %s" % (key, path))
			(res, msg) = is_superset(obj1[key], obj2[key], path + "." + key)
			if not res:
				return (False, msg)
	elif isinstance(obj1, list):
		if not isinstance(obj2, list):
			return (False, "Type mismatch: %s, is list instead of %s" % (path, type(obj2)))
		for el in obj2:
			if not el in obj1:
				return (False, "Element %s missing: %s" % (el, path))
	else:
		return (obj1 == obj2, "Value mismatch: %s, is %s instead of %s" % (path, repr(obj1), repr(obj2)))
	return (True, None)


def checkSuperset(obj1, obj2):
	res, error = isSuperset(obj1, obj2)
	assert res, error


unicodeStrings = {
"russian": u"По оживлённым берегам",
"ancient_greek": u"Ἰοὺ ἰού· τὰ πάντʼ ἂν ἐξήκοι σαφῆ.",
"sanskrit": u"पशुपतिरपि तान्यहानि कृच्छ्राद्",
"chinese": u"子曰：「學而時習之，不亦說乎？有朋自遠方來，不亦樂乎？",
"tamil": u"ஸ்றீனிவாஸ ராமானுஜன் ஐயங்கார்",
"arabic": u"بِسْمِ ٱللّٰهِ ٱلرَّحْمـَبنِ ٱلرَّحِيمِ"
}
unicodeTestString = "".join(unicodeStrings.values())