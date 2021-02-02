#include "PyExt_alpha.hh"
#include "PyExt_functions.hh"

namespace {
using namespace std;
struct Exprext001: public PyExt_ModuleBase {
public:
  Exprext001(const PyExt_Config::Component *cfg)
  : PyExt_ModuleBase(cfg),
  cap(sdc("cap")),
  ticker(sdc("ticker")),
  tickerIx(sdc.ix("tickerIx")),
    {% for name in dataname -%}
        {{name[1]}}
    {% endfor %}
  pastAlpha(sdc.instsz(), NAN)
	{
	}

  void GenAlpha(unsigned di, vector<float>& alpha) {
    for (unsigned ii = 0; ii < alpha.size(); ++ii) {
      if (!(*valid)(di, ii)) continue;
      float sum = 0, cnt = 0;
      unsigned itv_num = 24;
      for(unsigned i = 0; i < itv_num; ++i ){
        sum += stdbid1buy(di-1024, i+23, ii);
      }
      alpha[ii] = sum/float(itv_num);
    }
    pastAlpha = alpha;
	}

  void
  LoadVar(boost::archive::binary_iarchive &ar)
  {
		ar & *this;
	}

  void
  SaveVar(boost::archive::binary_oarchive &ar)
  {
		ar & *this;
	}

private:
  Smart_Sptr& cap;
  Smart_Sptr& ticker;
  Ix_Sptr& tickerIx;
  {% for name in dataname -%}
     {{name[2]}}
  {% endfor %}
  vector<float> pastAlpha;

  friend class boost::serialization::access;
  template <typename Archive>
  void
  serialize(Archive &ar,
            const unsigned int /*file_version*/)
  {
    ar & pastAlpha;
  }

};
} // non

extern "C" {
  PyExt_ModuleBase* create(const PyExt_Config::Component *cfg) {
    return new Exprext001(cfg);
  }
}
