import lucene
import sys

from java.io import File
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.util import Version

# Initialize Lucene.
lucene.initVM()

# Indicate where (i.e., what directory path) the index is located.
storeDir = "/tmp/REMOVEME.index-dir"
dir = SimpleFSDirectory(File(storeDir))

# Create a standard query analyzer and searcher.
analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)
searcher = IndexSearcher(DirectoryReader.open(dir))

# Search for the number 37 (just as an example).
query = QueryParser(Version.LUCENE_CURRENT, "text", analyzer).parse("37")
MAX = 1000
hits = searcher.search(query, MAX)

print "Found %d document(s) that matched query '%s':" % (hits.totalHits, query)

# Retrieve the documents that were found and spit out it's contents.
for hit in hits.scoreDocs:
  print hit.score, hit.doc, hit.toString()
  doc = searcher.doc(hit.doc)
  print doc.get("text").encode("utf-8")