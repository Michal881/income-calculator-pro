(function () {
  const industryEngineConfig = {
    industryGroups: [
      {
        key: "general_liability",
        label: "OC działalności (ogólna)",
        pricingModels: ["GL_BASE_TURNOVER"],
        coverages: ["general_liability"],
      },
      {
        key: "product_liability",
        label: "OC za produkt",
        pricingModels: ["GL_BASE_TURNOVER", "PL_PRODUCT_SPLIT"],
        coverages: ["general_liability", "product_liability"],
      },
      {
        key: "extended_product_liability",
        label: "Rozszerzone OC za produkt",
        pricingModels: ["GL_BASE_TURNOVER", "PL_PRODUCT_SPLIT", "XPL_EXTENDED_TRIGGER"],
        coverages: ["general_liability", "product_liability", "extended_product_liability"],
      },
      {
        key: "civil_environmental_liability",
        label: "Cywilna odpowiedzialność środowiskowa",
        pricingModels: ["GL_BASE_TURNOVER", "ENV_SEVERITY_BAND"],
        coverages: ["general_liability", "civil_environmental_liability"],
      },
      {
        key: "public_environmental_damage_liability",
        label: "Publicznoprawna szkoda w środowisku",
        pricingModels: ["GL_BASE_TURNOVER", "ENV_PUBLIC_DAMAGE"],
        coverages: ["general_liability", "public_environmental_damage_liability"],
      },
      {
        key: "construction_liability",
        label: "OC budowlane",
        pricingModels: ["GL_BASE_TURNOVER", "CONSTRUCTION_ACTIVITY_CLASS"],
        coverages: ["general_liability", "construction_liability"],
      },
    ],

    pricingModelMappings: {
      GL_BASE_TURNOVER: "Model bazowy od obrotu (MVP: tylko mapowanie)",
      PL_PRODUCT_SPLIT: "Model udziału ryzyka produktowego (MVP)",
      XPL_EXTENDED_TRIGGER: "Model rozszerzenia odpowiedzialności produktowej (MVP)",
      ENV_SEVERITY_BAND: "Model pasm narażenia środowiskowego (MVP)",
      ENV_PUBLIC_DAMAGE: "Model szkód publicznoprawnych środowiskowych (MVP)",
      CONSTRUCTION_ACTIVITY_CLASS: "Model klas aktywności budowlanej (MVP)",
    },

    coverages: {
      general_liability: "OC działalności",
      product_liability: "OC za produkt",
      extended_product_liability: "Rozszerzone OC za produkt",
      civil_environmental_liability: "Cywilna odpowiedzialność środowiskowa",
      public_environmental_damage_liability: "Publicznoprawna szkoda w środowisku",
      construction_liability: "OC budowlane",
    },

    riskFlags: {
      highPublicExposure: "Wysoka ekspozycja publiczna",
      mediumEnvironmentalExposure: "Średnia ekspozycja środowiskowa",
      highEnvironmentalExposure: "Wysoka ekspozycja środowiskowa",
      subcontractors: "Istotny udział podwykonawców",
      worksAtHeight: "Prace na wysokości",
      hotWorks: "Prace pożarowo niebezpieczne",
      missingKeyData: "Brak kluczowych danych",
    },

    coreQuestions: [
      {
        id: "annualTurnover",
        label: "Roczny obrót (PLN)",
        type: "number",
        required: true,
      },
      {
        id: "publicExposure",
        label: "Czy działalność ma ekspozycję publiczną (klienci/odwiedzający)?",
        type: "select",
        required: true,
        options: [
          { value: "no", label: "Nie" },
          { value: "yes", label: "Tak" },
        ],
      },
      {
        id: "environmentalExposure",
        label: "Poziom ekspozycji środowiskowej",
        type: "select",
        required: true,
        options: [
          { value: "small", label: "Mała" },
          { value: "medium", label: "Średnia" },
          { value: "large", label: "Duża" },
        ],
      },
      {
        id: "productShare",
        label: "Udział odpowiedzialności za produkt (%)",
        type: "number",
        required: false,
      },
    ],

    branchQuestions: {
      construction: [
        {
          id: "constructionWorksAtHeight",
          label: "Czy występują prace na wysokości?",
          type: "select",
          required: true,
          options: [
            { value: "no", label: "Nie" },
            { value: "yes", label: "Tak" },
          ],
        },
        {
          id: "constructionSubcontractors",
          label: "Czy udział podwykonawców przekracza 30%?",
          type: "select",
          required: true,
          options: [
            { value: "no", label: "Nie" },
            { value: "yes", label: "Tak" },
          ],
        },
      ],
      hospitality: [
        {
          id: "hospitalityDailyGuests",
          label: "Średnia liczba gości/klientów dziennie",
          type: "number",
          required: true,
        },
        {
          id: "hospitalityAlcohol",
          label: "Czy podawany jest alkohol?",
          type: "select",
          required: true,
          options: [
            { value: "no", label: "Nie" },
            { value: "yes", label: "Tak" },
          ],
        },
      ],
      environmental: [
        {
          id: "environmentalHazardousStorage",
          label: "Czy magazynowane są substancje niebezpieczne?",
          type: "select",
          required: true,
          options: [
            { value: "no", label: "Nie" },
            { value: "yes", label: "Tak" },
          ],
        },
        {
          id: "environmentalIncidents",
          label: "Liczba incydentów środowiskowych w ostatnich 5 latach",
          type: "number",
          required: true,
        },
      ],
    },

    decisionRules: [
      {
        id: "rule_missing",
        description: "Braki danych wymagają uzupełnienia przed wyceną.",
        evaluate: (ctx) => ctx.missingData.length > 0,
        referral: true,
      },
      {
        id: "rule_high_environment",
        description: "Duża ekspozycja środowiskowa wymaga oceny underwritera.",
        evaluate: (ctx) => ctx.answers.environmentalExposure === "large",
        referral: true,
      },
      {
        id: "rule_construction_height",
        description: "Prace na wysokości w OC budowlanym kierują sprawę do underwritera.",
        evaluate: (ctx) => ctx.industryGroup === "construction_liability" && ctx.answers.constructionWorksAtHeight === "yes",
        referral: true,
      },
    ],
  };

  function getIndustryGroup(key) {
    return industryEngineConfig.industryGroups.find((item) => item.key === key);
  }

  function getVisibleBranchKeys(answers, industryGroupKey) {
    const branchKeys = [];

    if (industryGroupKey === "construction_liability") {
      branchKeys.push("construction");
    }

    if (answers.publicExposure === "yes") {
      branchKeys.push("hospitality");
    }

    if (["medium", "large"].includes(answers.environmentalExposure)) {
      branchKeys.push("environmental");
    }

    return branchKeys;
  }

  function getVisibleQuestions(answers, industryGroupKey) {
    const branchKeys = getVisibleBranchKeys(answers, industryGroupKey);
    const branchQuestions = branchKeys.flatMap((key) => industryEngineConfig.branchQuestions[key] || []);
    return {
      core: industryEngineConfig.coreQuestions,
      branchKeys,
      branchQuestions,
    };
  }

  function evaluateCase(industryGroupKey, answers) {
    const group = getIndustryGroup(industryGroupKey);
    const visible = getVisibleQuestions(answers, industryGroupKey);
    const requiredQuestions = [...visible.core, ...visible.branchQuestions].filter((question) => question.required);

    const missingData = requiredQuestions
      .filter((question) => {
        const value = answers[question.id];
        return value === undefined || value === null || value === "";
      })
      .map((question) => question.label);

    const riskFlags = [];

    if (answers.publicExposure === "yes") {
      riskFlags.push(industryEngineConfig.riskFlags.highPublicExposure);
    }

    if (answers.environmentalExposure === "medium") {
      riskFlags.push(industryEngineConfig.riskFlags.mediumEnvironmentalExposure);
    }

    if (answers.environmentalExposure === "large") {
      riskFlags.push(industryEngineConfig.riskFlags.highEnvironmentalExposure);
    }

    if (answers.constructionSubcontractors === "yes") {
      riskFlags.push(industryEngineConfig.riskFlags.subcontractors);
    }

    if (answers.constructionWorksAtHeight === "yes") {
      riskFlags.push(industryEngineConfig.riskFlags.worksAtHeight);
    }

    if (answers.hospitalityAlcohol === "yes") {
      riskFlags.push(industryEngineConfig.riskFlags.hotWorks);
    }

    if (missingData.length > 0) {
      riskFlags.push(industryEngineConfig.riskFlags.missingKeyData);
    }

    const context = { answers, industryGroup: industryGroupKey, missingData, riskFlags };
    const matchedRules = industryEngineConfig.decisionRules.filter((rule) => rule.evaluate(context));
    const referral = matchedRules.some((rule) => rule.referral);

    return {
      industryLabel: group ? group.label : "—",
      pricingModels: group ? group.pricingModels.map((key) => industryEngineConfig.pricingModelMappings[key] || key) : [],
      coverages: group ? group.coverages.map((key) => industryEngineConfig.coverages[key] || key) : [],
      riskFlags,
      referral,
      missingData,
      matchedRules: matchedRules.map((rule) => rule.description),
      visibleBranches: visible.branchKeys,
    };
  }

  window.IndustryQuestionEngine = {
    config: industryEngineConfig,
    getIndustryGroup,
    getVisibleQuestions,
    evaluateCase,
  };
})();
