import lucene
import sys

from java.io import File
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, FieldType
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.util import Version
from org.apache.lucene.analysis.miscellaneous import LimitTokenCountAnalyzer

# Initialize Lucene.
lucene.initVM()

# Indicate where (i.e., what directory path) the index is located.
# Lucene will create a bunch of files in there and overwrite existing stuff (beware!).
storeDir = "/tmp/REMOVEME.index-dir"
store = SimpleFSDirectory(File(storeDir))

# Create a standard analyzer, config, and index writer.
analyzer = LimitTokenCountAnalyzer(StandardAnalyzer(Version.LUCENE_CURRENT), 1048576)
config = IndexWriterConfig(Version.LUCENE_CURRENT, analyzer)
config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
writer = IndexWriter(store, config)
print >> sys.stderr, "Currently there are %d documents in the index..." % writer.numDocs()

# Make a bunch of fake, simple hello world type of documents. Add some numbers in there as well (so we can search for them later).
# Tell Lucene to store the contents and index it as well.
for i in range(5000):
  doc = Document()
  fieldName = "text"
  fieldContent = i*(" hello # " +str(i)+ " this is my text and I'm sticking to it ! ")
  doc.add(Field(fieldName, fieldContent, Field.Store.YES, Field.Index.ANALYZED))
  writer.addDocument(doc)

print >> sys.stderr, "Currently there are %d documents in the index..." % writer.numDocs()
print >> sys.stderr, "Closing index of %d documents..." % writer.numDocs()

# Done.
writer.close()