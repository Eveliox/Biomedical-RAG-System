"""XML parsing is a pure function — great candidate for unit tests.

We hand-roll a tiny PubMed-shaped XML instead of hitting the network.
"""
from app.services.pubmed_service import parse_pubmed_xml


SAMPLE_XML = """
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <Journal>
          <Title>Nature Genetics</Title>
          <JournalIssue>
            <PubDate><Year>2024</Year><Month>Mar</Month></PubDate>
          </JournalIssue>
        </Journal>
        <ArticleTitle>KRAS mutations in pancreatic cancer.</ArticleTitle>
        <Abstract>
          <AbstractText Label="BACKGROUND">Background text.</AbstractText>
          <AbstractText Label="RESULTS">KRAS was mutated in 92% of tumors.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author><LastName>Smith</LastName><Initials>JA</Initials></Author>
          <Author><LastName>Chen</LastName><Initials>L</Initials></Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="doi">10.1038/xyz</ArticleId>
        <ArticleId IdType="pubmed">12345678</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""


def test_parses_pmid_title_and_journal():
    papers = parse_pubmed_xml(SAMPLE_XML)
    assert len(papers) == 1
    p = papers[0]
    assert p.pmid == "12345678"
    assert "KRAS" in p.title
    assert p.journal == "Nature Genetics"
    assert p.publication_date == "2024-Mar"


def test_concatenates_labeled_abstract_sections():
    p = parse_pubmed_xml(SAMPLE_XML)[0]
    assert "BACKGROUND:" in p.abstract
    assert "RESULTS:" in p.abstract
    assert "92%" in p.abstract


def test_extracts_authors_and_doi():
    p = parse_pubmed_xml(SAMPLE_XML)[0]
    assert p.authors == ["Smith JA", "Chen L"]
    assert p.doi == "10.1038/xyz"


def test_pubmed_url_property():
    p = parse_pubmed_xml(SAMPLE_XML)[0]
    assert p.pubmed_url == "https://pubmed.ncbi.nlm.nih.gov/12345678/"


def test_missing_abstract_is_empty_string_not_none():
    xml = """
    <PubmedArticleSet>
      <PubmedArticle>
        <MedlineCitation>
          <PMID>999</PMID>
          <Article>
            <Journal><Title>J</Title></Journal>
            <ArticleTitle>Title only paper.</ArticleTitle>
          </Article>
        </MedlineCitation>
      </PubmedArticle>
    </PubmedArticleSet>
    """
    p = parse_pubmed_xml(xml)[0]
    assert p.abstract == ""
